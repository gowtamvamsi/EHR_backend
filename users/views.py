from rest_framework import viewsets, status, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django_otp import devices_for_user, user_has_device
from django_otp.plugins.otp_totp.models import TOTPDevice
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import Permission
from rest_framework.permissions import IsAdminUser
from .models import User, AuditLog, Role 
from .serializers import (
    UserSerializer,
    RegisterSerializer,
    MFAEnableSerializer,
    MFAVerifySerializer,
    AuditLogSerializer,
    UpdateUserSerializer,
    PermissionSerializer,
    RoleSerializer 
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


class UserViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        """Retrieve all users - accessible to admins only."""
        if not request.user.is_staff:
            return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        queryset = User.objects.all()
        serializer = UserSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """Retrieve details of a single user - accessible to admins only."""
        if not request.user.is_staff:
            return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        user = get_object_or_404(User, pk=pk)
        serializer = UserSerializer(user)
        return Response(serializer.data)

    def update(self, request, pk=None):
        """Allow admins to update user details such as email, status, etc."""
        if not request.user.is_staff:
            return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        user = get_object_or_404(User, pk=pk)
        serializer = UpdateUserSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            AuditLog.objects.create(
                user=request.user,  # Ensure this is a valid User instance
                action="UPDATE_USER",
                resource_type="USER",
                resource_id=str(user.id),
                ip_address=request.META.get("REMOTE_ADDR"),
                details={"username": user.username, "updated_fields": list(request.data.keys())},
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def register(self, request):
        """Allow admins to create new users in the system."""
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Correct AuditLog creation
            AuditLog.objects.create(
                user=request.user,  # Ensure this is a valid User instance
                action="CREATE_USER",
                resource_type="USER",
                resource_id=str(user.id),
                ip_address=request.META.get("REMOTE_ADDR"),
                details={"username": user.username, "role": user.role},
            )
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["delete"], permission_classes=[permissions.IsAdminUser])
    def delete(self, request, pk=None):
        """Allow admins to delete or deactivate a user."""
        user = get_object_or_404(User.objects.all(), pk=pk)
        user.is_active = False  # Marking user as inactive instead of deletion (soft delete)
        user.save()
        # Correct AuditLog creation
        AuditLog.objects.create(
            user=request.user,  # Ensure this is a valid User instance
            action="DELETE_USER",
            resource_type="USER",
            resource_id=str(user.id),
            ip_address=request.META.get("REMOTE_ADDR"),
            details={"username": user.username},
        )
        return Response({"detail": "User deactivated successfully."}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["post"])
    def mfa_enable(self, request):
        """Enable MFA for the authenticated user."""
        serializer = MFAEnableSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            device = TOTPDevice.objects.create(user=request.user, confirmed=False)
            return Response({"config_url": device.config_url}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def mfa_verify(self, request):
        """Verify and confirm MFA setup for the authenticated user."""
        serializer = MFAVerifySerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            device = devices_for_user(request.user, confirmed=False).first()
            if device:
                device.confirmed = True
                device.save()
                request.user.is_mfa_enabled = True
                request.user.save()
                return Response({"status": "MFA enabled successfully"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAdminUser])
    def audit_logs(self, request):
        """Retrieve audit logs for the authenticated admin."""
        logs = AuditLog.objects.filter(user=request.user)
        serializer = AuditLogSerializer(logs, many=True)
        return Response(serializer.data)

    # New method: Assign roles to a user
    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def assign_roles(self, request, pk=None):
        """
        Assign roles (groups) to a user.
        Endpoint: POST /users/<id>/assign_roles/
        """
        print("assign_roles action called")  # Debugging
        print("User Queryset:", User.objects.filter(pk=pk)) 
        user = get_object_or_404(User, pk=pk)
        roles = request.data.get("roles", [])
        print(roles)
        if not isinstance(roles, list):
            return Response({"detail": "Roles must be an array."}, status=status.HTTP_400_BAD_REQUEST)
        if not roles:
            user.groups.clear()
            return Response({"detail": "Roles cleared successfully.", "roles": []}, status=status.HTTP_200_OK)

        # Assign new roles
        for role_id in roles:
            role = get_object_or_404(Role, id=role_id, is_active=True)
            print(f"Assigning role: {role.group.name} to user: {user.username}")
            user.groups.add(role.group)
        user.save()
        return Response(
            {"detail": "Roles assigned successfully.", "roles": [role_id for role_id in roles]},
            status=status.HTTP_200_OK,
        )

    # New method: Retrieve roles of a user
    @action(detail=True, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def retrieve_roles(self, request, pk=None):
        """
        Retrieve all roles assigned to a user.
        Endpoint: GET /users/<id>/retrieve_roles/
        """
        user = get_object_or_404(User, pk=pk)

        # Fetch roles (groups) for the user
        roles = user.groups.all()
        data = [{"id": role.role.id, "name": role.name, "description": role.role.description} for role in roles]

        return Response(data, status=status.HTTP_200_OK)


class RoleViewSet(viewsets.ViewSet):
    """
    ViewSet to manage roles.
    Includes creating, retrieving, updating, and soft-deleting roles.
    """

    def list(self, request):
        """Retrieve all roles - accessible to admins only."""
        if not request.user.is_staff:
            return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        roles = Role.objects.all()
        data = [{
            "id": role.id,
            "name": role.group.name,
            "description": role.description
        } for role in roles]
        return Response(data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """Retrieve details of a single role - accessible to admins only."""
        if not request.user.is_staff:
            return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        role = get_object_or_404(Role, id=pk)
        data = {
            "id": role.id,
            "name": role.group.name,
            "description": role.description
        }
        return Response(data, status=status.HTTP_200_OK)

    def create(self, request):
        """Create a new role."""
        if not request.user.is_staff:
            return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        serializer = RoleSerializer(data=request.data)
        if serializer.is_valid():
            role = serializer.save()
            return Response({
                "id": role.id,
                "name": role.group.name,
                "description": role.description,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        """Update an existing role."""
        if not request.user.is_staff:
            return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        role = get_object_or_404(Role, id=pk)
        serializer = RoleSerializer(role, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "id": role.id,
                "name": role.group.name,
                "description": role.description,
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        """Soft delete (archive) a role."""
        if not request.user.is_staff:
            return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        role = get_object_or_404(Role, id=pk)
        role.is_active = False  # Assume the `Role` model has an `is_active` field for soft deletion
        role.save()
        return Response({"detail": "Role archived successfully."}, status=status.HTTP_204_NO_CONTENT)

    # Assign permissions to a role
    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def assign_permissions(self, request, pk=None):
        """Assign permissions to a role."""
        role = get_object_or_404(Role, id=pk, is_active=True)
        permissions = request.data.get("permissions", [])
        if not permissions:
            return Response({"detail": "No permissions provided."}, status=status.HTTP_400_BAD_REQUEST)

        for codename in permissions:
            try:
                permission = Permission.objects.get(codename=codename)
                role.group.permissions.add(permission)
            except Permission.DoesNotExist:
                return Response({"detail": f"Permission {codename} not found."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "Permissions assigned successfully."}, status=status.HTTP_200_OK)

    # Retrieve permissions assigned to a role
    @action(detail=True, methods=["get"], permission_classes=[permissions.IsAdminUser])
    def retrieve_permissions(self, request, pk=None):
        """Retrieve permissions assigned to a role."""
        role = get_object_or_404(Role, id=pk, is_active=True)
        permissions = role.group.permissions.all()
        data = [{"id": perm.id, "name": perm.name, "codename": perm.codename} for perm in permissions]

        return Response(data, status=status.HTTP_200_OK)

class PermissionViewSet(viewsets.ViewSet):
    """
    ViewSet to manage permissions.
    Supports CRUD operations for permissions.
    """

    permission_classes = [IsAdminUser]  # Only admins can manage permissions

    def list(self, request):
        """Retrieve all permissions."""
        permissions = Permission.objects.all()
        serializer = PermissionSerializer(permissions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        """Create a new permission."""
        serializer = PermissionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        """Retrieve a specific permission."""
        permission = Permission.objects.filter(pk=pk).first()
        if not permission:
            return Response({"detail": "Permission not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = PermissionSerializer(permission)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, pk=None):
        """Update an existing permission."""
        permission = Permission.objects.filter(pk=pk).first()
        if not permission:
            return Response({"detail": "Permission not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = PermissionSerializer(permission, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        """Delete an existing permission."""
        permission = Permission.objects.filter(pk=pk).first()
        if not permission:
            return Response({"detail": "Permission not found."}, status=status.HTTP_404_NOT_FOUND)
        permission.delete()
        return Response({"detail": "Permission deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom token view that logs user logins."""

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user = User.objects.get(username=request.data["username"])
            AuditLog.objects.create(
                user=user,
                action="LOGIN",
                resource_type="USER",
                resource_id=str(user.id),
                ip_address=request.META.get("REMOTE_ADDR"),
                details={"method": "jwt"},
            )
        return response
