from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import User, AuditLog

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 
            'username', 
            'email', 
            'first_name', 
            'last_name',
            'role',
            'phone_number',
            'is_mfa_enabled',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password',
            'first_name',
            'last_name',
            'role',
            'phone_number'
        ]

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class MFAEnableSerializer(serializers.Serializer):
    pass  # No fields needed, just validates the request

class MFAVerifySerializer(serializers.Serializer):
    token = serializers.CharField()

    def validate_token(self, value):
        user = self.context['request'].user
        device = user.totpdevice_set.first()
        if not device or not device.verify_token(value):
            raise serializers.ValidationError("Invalid token")
        return value

class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = [
            'id',
            'action',
            'resource_type',
            'resource_id',
            'timestamp',
            'ip_address',
            'details'
        ]
        read_only_fields = ['timestamp']