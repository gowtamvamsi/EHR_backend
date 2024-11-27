from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from django_otp import devices_for_user
from django_otp.plugins.otp_totp.models import TOTPDevice
from .models import User, AuditLog
from .serializers import (
    UserSerializer, 
    RegisterSerializer,
    MFAEnableSerializer,
    MFAVerifySerializer,
    AuditLogSerializer
)

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

class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user = User.objects.get(username=request.data['username'])
            AuditLog.objects.create(
                user=user,
                action='LOGIN',
                resource_type='USER',
                resource_id=str(user.id),
                ip_address=request.META.get('REMOTE_ADDR'),
                details={'method': 'jwt'}
            )
        return response