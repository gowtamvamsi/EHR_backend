from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from users.models import User, AuditLog, Role
from django.contrib.auth.models import Permission, Group
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from users.models import User, Role
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()
'''

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
        """Ensure a user is created successfully with the correct attributes."""
        self.assertEqual(self.user.email, 'doctor@test.com')
        self.assertEqual(self.user.role, User.Role.DOCTOR)
        self.assertFalse(self.user.is_mfa_enabled)

    def test_user_permissions(self):
        """Test user permissions functionality."""
        self.assertFalse(self.user.has_perm('users.can_view_patient_records'))
        permission = Permission.objects.create(
            codename='can_view_patient_records',
            name='Can View Patient Records',
            content_type_id=1
        )
        self.user.user_permissions.add(permission)
        self.user.refresh_from_db()
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
        """Test the creation of an audit log entry."""
        self.assertEqual(self.audit_log.action, 'LOGIN')
        self.assertEqual(self.audit_log.resource_type, 'USER')
        self.assertEqual(self.audit_log.ip_address, '127.0.0.1')
        self.assertEqual(self.audit_log.details, {'method': 'password'})
'''

class UserManagementAPITests(APITestCase):
    def setUp(self):
        # Create admin user and generate token
        self.admin_user = User.objects.create_superuser(
            username="admin_2",
            password="admin123_2",
            email="admin@example.com"
        )
        self.admin_user.save()

        response = self.client.post("/api/token/", {
            "username": "admin_2",
            "password": "admin123_2"
        })
        self.admin_token = response.data.get("access")

        # Create roles
        self.doctor_group = Group.objects.create(name="Doctor")
        self.nurse_group = Group.objects.create(name="Nurse")
        self.doctor_role = Role.objects.create(group=self.doctor_group, description="Handles patient care")
        self.nurse_role = Role.objects.create(group=self.nurse_group, description="Assists doctors")

        # Assign permissions to groups
        doctor_permissions = Permission.objects.filter(
            codename__in=["view_patient", "change_patient", "add_prescription"]
        )
        self.doctor_group.permissions.set(doctor_permissions)

        nurse_permissions = Permission.objects.filter(
            codename__in=["view_patient", "change_patient"]
        )
        self.nurse_group.permissions.set(nurse_permissions)

            # Check if groups and roles are correctly created
        print(f"Doctor Group Permissions: {self.doctor_group.permissions.all()}")
        print(f"Nurse Group Permissions: {self.nurse_group.permissions.all()}")
        print(f"User Permissions: {self.admin_user.get_all_permissions()}")

    def get_headers(self):
        """Return authorization headers for the test client."""
        print(f'HTTP_AUTHORIZATION: Bearer {self.admin_token}')
        return {"HTTP_AUTHORIZATION": f"Bearer {self.admin_token}"}

    def test_create_user(self):
        """Test creating a new user."""
        data = {
            "username": "testuser_2",
            "email": "testuser@example.com",
            "password": "securepass123",
            "first_name": "Test",
            "last_name": "User",
            "role": "STAFF",
            "phone_number": "+911234567890"
        }
        response = self.client.post("/api/users/register/", data, **self.get_headers())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["email"], "testuser@example.com")

    def test_get_all_users(self):
        """Test retrieving a list of all users."""
        response = self.client.get("/api/users/", **self.get_headers())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_single_user(self):
        """Test retrieving a single user's details."""
        user = User.objects.create_user(
            username="singleuser",
            email="singleuser@example.com"
        )
        response = self.client.get(f"/api/users/{user.id}/", **self.get_headers())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "singleuser@example.com")

    def test_update_user(self):
        """Test updating a user's details."""
        user = User.objects.create_user(
            username="updateuser",
            email="updateuser@example.com"
        )
        data = {"email": "updateduser@example.com"}
        response = self.client.put(f"/api/users/{user.id}/", data, **self.get_headers())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "updateduser@example.com")

    def test_deactivate_user(self):
        """Test marking a user as inactive."""
        user = User.objects.create_user(
            username="inactiveuser",
            email="inactiveuser@example.com"
        )
        response = self.client.delete(f"/api/users/{user.id}/", **self.get_headers())
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        user.refresh_from_db()
        self.assertFalse(user.is_active)

    def test_assign_roles_to_user(self):

        """Test assigning roles to a user."""
        # Create and explicitly save a user
        user = User.objects.create_user(
            username="roleuser",
            email="roleuser@example.com"
        )
        user.save() 

        print(f"User ID: {user.id}")
        print(f"Is user in database: {User.objects.filter(id=user.id).exists()}")
        print(f"All users in database: {User.objects.all()}")
        print(f"Role ID: {self.doctor_role.id}")
        print(f"Is role in database: {Role.objects.filter(id=self.doctor_role.id).exists()}")
        print(f"All roles in database: {Role.objects.all()}")
      
        # Resolve URL dynamically
        url = reverse('user-assign-roles', kwargs={'pk': user.id})
        print(f"Resolved URL: {url}")

        # Verify the authenticated user
        print(self.admin_user)  
        print(f"Is Authenticated: {self.admin_user.is_authenticated}")
        print(self.admin_user.has_perm('users.assign_roles'))
        
        # Perform API call
        data = {"roles":[f"{self.doctor_role.id}"]}
        response = self.client.post(url, data, **self.get_headers())
        print(f"Response Status: {response.status_code}")
        try:
            print(f"Response Data: {response.json()}")
        except Exception as e:
            print(f"Error parsing response JSON: {e}")

        # Assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.doctor_group, user.groups.all())

    def test_revoke_roles_from_user(self):
        """Test revoking roles from a user."""
        user = User.objects.create_user(
            username="revokeroleuser",
            email="revokeroleuser@example.com"
        )
        user.groups.add(self.doctor_group)

        # Revoke all roles
        data = {"roles": []}
        response = self.client.post(f"/api/users/{user.id}/assign_roles/", data, **self.get_headers())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(user.groups.count(), 0)