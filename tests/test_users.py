from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from users.models import User, AuditLog

class UserModelTests(TestCase):
    def setUp(self):
        self.user_data = {
            'username': 'testdoctor',
            'email': 'doctor@test.com',
            'password': 'securepass123',
            'first_name': 'Test',
            'last_name': 'Doctor',
            'role': User.Role.DOCTOR,
            'phone_number': '+911234567890'
        }
        self.user = User.objects.create_user(**self.user_data)

    def test_user_creation(self):
        self.assertEqual(self.user.email, 'doctor@test.com')
        self.assertEqual(self.user.role, User.Role.DOCTOR)
        self.assertFalse(self.user.is_mfa_enabled)

    def test_user_permissions(self):
        self.assertFalse(self.user.has_perm('users.can_view_patient_records'))
        self.user.user_permissions.add('users.can_view_patient_records')
        self.assertTrue(self.user.has_perm('users.can_view_patient_records'))

class AuditLogTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.audit_log = AuditLog.objects.create(
            user=self.user,
            action='LOGIN',
            resource_type='USER',
            resource_id='1',
            ip_address='127.0.0.1',
            details={'method': 'password'}
        )

    def test_audit_log_creation(self):
        self.assertEqual(self.audit_log.action, 'LOGIN')
        self.assertEqual(self.audit_log.resource_type, 'USER')
        self.assertEqual(self.audit_log.ip_address, '127.0.0.1')