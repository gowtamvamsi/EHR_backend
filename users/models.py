from django.contrib.auth.models import AbstractUser,Group
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings 

class Role(models.Model):
    class RoleType(models.TextChoices):
        ADMIN = 'ADMIN', _('Administrator')
        DOCTOR = 'DOCTOR', _('Doctor')
        PATIENT = 'PATIENT', _('Patient')
        STAFF = 'STAFF', _('Staff')
    group = models.OneToOneField(
        Group, 
        on_delete=models.CASCADE, 
        related_name="role"
    )
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.group.name} - {self.description}"
    
class User(AbstractUser):
    role = models.CharField(
        max_length=20,
        choices=Role.RoleType.choices,
        default=Role.RoleType.PATIENT
    )
    phone_number = models.CharField(
        max_length=15,
        verbose_name="Phone Number",
        help_text="Contact phone number for the user.",
        blank=True,  # Ensures phone_number is required at the model level
        null=False    # Ensures the database column cannot store NULL values
    )
    is_mfa_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Fix reverse accessor clashes
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    class Meta:
        permissions = [
            ("can_view_patient_records", "Can view patient records"),
            ("can_edit_patient_records", "Can edit patient records"),
            ("can_view_billing", "Can view billing information"),
            ("can_manage_appointments", "Can manage appointments"),
        ]

class AuditLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    action = models.CharField(max_length=50)
    resource_type = models.CharField(max_length=50)
    resource_id = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    details = models.JSONField()

    class Meta:
        ordering = ['-timestamp']
