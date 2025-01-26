from rest_framework import viewsets, status, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django_otp import devices_for_user, user_has_device
from django_otp.plugins.otp_totp.models import TOTPDevice
from .models import User, AuditLog
from .serializers import (
    UserSerializer, 
    RegisterSerializer,
    MFAEnableSerializer,
    MFAVerifySerializer,
    AuditLogSerializer
)
import logging

logger = logging.getLogger(__name__)

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        logger.debug("Starting CustomTokenObtainPairSerializer.validate")
        try:
            # First validate credentials
            data = super().validate(attrs)
            logger.debug("Base validation successful")

            user = self.user
            logger.debug(f"Processing user: {user.username}")

            # Check if user has MFA enabled
            if user.is_mfa_enabled:
                logger.debug("User has MFA enabled")
                # If MFA token is not provided in initial request
                if 'mfa_token' not in self.initial_data:
                    logger.debug("No MFA token provided, returning temporary token")
                    return {
                        'requires_mfa': True,
                        'temp_token': data['access']
                    }
                
                logger.debug("Verifying MFA token")
                # Verify MFA token
                device = devices_for_user(user, confirmed=True).first()
                if not device or not device.verify_token(self.initial_data['mfa_token']):
                    logger.debug("Invalid MFA token")
                    raise serializers.ValidationError({
                        'mfa_token': ['Invalid MFA token']
                    })
                logger.debug("MFA token verified successfully")

            try:
                # Log successful login
                AuditLog.objects.create(
                    user=user,
                    action='LOGIN',
                    resource_type='USER',
                    resource_id=str(user.id),
                    ip_address=self.context['request'].META.get('REMOTE_ADDR', ''),
                    details={'method': 'jwt', 'mfa_used': user.is_mfa_enabled}
                )
                logger.debug("Audit log created successfully")
            except Exception as e:
                logger.error(f"Error creating audit log: {str(e)}")

            logger.debug("Returning validated data")
            return data

        except serializers.ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in validate: {str(e)}", exc_info=True)
            raise serializers.ValidationError({
                'detail': 'An unexpected error occurred during authentication.'
            })

    @classmethod
    def get_token(cls, user):
        try:
            token = super().get_token(user)
            # Add custom claims
            token['username'] = user.username
            token['role'] = user.role
            return token
        except Exception as e:
            logger.error(f"Error in get_token: {str(e)}", exc_info=True)
            raise

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        try:
            logger.debug("Starting CustomTokenObtainPairView.post")
            response = super().post(request, *args, **kwargs)
            logger.debug(f"Response status code: {response.status_code}")
            return response
        except Exception as e:
            logger.error(f"Error in CustomTokenObtainPairView.post: {str(e)}", exc_info=True)
            return Response(
                {'detail': 'An error occurred during authentication.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_serializer_context(self):
        try:
            context = super().get_serializer_context()
            context.update({"request": self.request})
            return context
        except Exception as e:
            logger.error(f"Error in get_serializer_context: {str(e)}", exc_info=True)
            raise

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def mfa_enable(self, request):
        serializer = MFAEnableSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            device = TOTPDevice.objects.create(user=request.user, confirmed=False)
            config_url = device.config_url
            return Response({'config_url': config_url})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def mfa_verify(self, request):
        serializer = MFAVerifySerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            device = devices_for_user(request.user, confirmed=False).first()
            if device is not None:
                device.confirmed = True
                device.save()
                request.user.is_mfa_enabled = True
                request.user.save()
                return Response({'status': 'MFA enabled successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def audit_logs(self, request):
        if not request.user.is_staff:
            return Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        logs = AuditLog.objects.filter(user=request.user)
        serializer = AuditLogSerializer(logs, many=True)
        return Response(serializer.data)