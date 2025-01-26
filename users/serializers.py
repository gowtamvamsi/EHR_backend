from rest_framework import serializers
from .models import User, AuditLog, Role
from django.contrib.auth.models import Group,Permission
 
class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model to retrieve user details."""

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "phone_number",
            "is_mfa_enabled",
            "created_at",
            "updated_at",
            "is_active"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for registering a new user."""
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "role",
            "phone_number",
        ]

    def create(self, validated_data):
        """Create a new user with hashed password."""
        print(validated_data)
        role = validated_data.get("role", Role.RoleType.PATIENT)  # Default to PATIENT if not provided
        if role not in [choice[0] for choice in Role.RoleType.choices]:
            raise serializers.ValidationError({"role": "Invalid role."})
        print("Creating user with:", validated_data)  # Debugging
        user = User.objects.create_user(**validated_data)
        return user

    def validate_email(self, value):
        """Ensure email is unique."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value


class UpdateUserSerializer(serializers.ModelSerializer):
    """Serializer for updating user details such as email, status, and role."""

    class Meta:
        model = User
        fields = ['email', 'role', 'is_active', 'first_name', 'last_name', 'phone_number']
        read_only_fields = ['username']

    def validate_email(self, value):
        """Ensure email is unique during update."""
        if User.objects.exclude(id=self.instance.id).filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value


class MFAEnableSerializer(serializers.Serializer):
    """Serializer for enabling MFA."""
    def validate(self, attrs):
        """Ensure MFA can be enabled for the user."""
        user = self.context["request"].user
        if user.is_mfa_enabled:
            raise serializers.ValidationError("MFA is already enabled for this user.")
        return attrs


class MFAVerifySerializer(serializers.Serializer):
    """Serializer for verifying MFA token."""
    token = serializers.CharField()

    def validate_token(self, value):
        """Validate the provided MFA token."""
        user = self.context["request"].user
        device = user.totpdevice_set.filter(confirmed=False).first()
        if not device or not device.verify_token(value):
            raise serializers.ValidationError("Invalid or expired MFA token.")
        return value


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for AuditLog model to retrieve audit log details."""

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "user",
            "action",
            "resource_type",
            "resource_id",
            "timestamp",
            "ip_address",
            "details",
        ]
        read_only_fields = ["id", "timestamp", "user", "ip_address"]

    def to_representation(self, instance):
        """Customize the representation of the audit log."""
        representation = super().to_representation(instance)
        # Mask sensitive details if necessary
        if "details" in representation and isinstance(representation["details"], dict):
            representation["details"] = {k: str(v) for k, v in representation["details"].items()}
        return representation

class RoleSerializer(serializers.ModelSerializer):
    """Serializer for Role model to handle role creation and validation."""
    name = serializers.CharField(max_length=150)
    description = serializers.CharField(max_length=500, required=False, allow_blank=True)

    class Meta:
        model = Role
        fields = ["id", "name", "description"]

    def create(self, validated_data):
        """Create a new role and link it to a group."""
        name = validated_data.get("name")
        description = validated_data.get("description", "")

        # Create the group
        group = Group.objects.create(name=name)

        # Create the role linked to the group
        role = Role.objects.create(group=group, description=description)
        return role

    def validate_name(self, value):
        """Ensure the role name is unique."""
        if Group.objects.filter(name=value).exists():
            raise serializers.ValidationError("A role with this name already exists.")
        return value

class PermissionSerializer(serializers.ModelSerializer):
    """
    Serializer for the Permission model.
    Handles validation and transformation for permission objects.
    """

    class Meta:
        model = Permission
        fields = ["id", "name", "codename", "content_type"]  # Include key fields
        read_only_fields = ["id"]  # ID is read-only since it is auto-generated