from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from users.models import User, Role
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model

User = get_user_model()

class UserManagementAPITests(APITestCase):
    def setUp(self):
        # Create an admin user and a regular user
        self.admin_user = User.objects.create_superuser(
            username="admin_user", 
            email="admin@example.com", 
            password="adminpass", 
        )
        self.admin_user.save()

        self.role_user = User.objects.create_user(
            username="role_user", 
            email="roleuser@example.com", 
            password="rolepass"
        )
        self.doctor_group = Group.objects.create(name="Doctor")
        self.nurse_group = Group.objects.create(name="Nurse")
        self.doctor_role = Role.objects.create(group=self.doctor_group, description="Handles patient care")
        self.nurse_role = Role.objects.create(group=self.nurse_group, description="Assists doctors")

    def get_token(self, username, password):
        """Helper function to retrieve a JWT token."""
        url = reverse('token_obtain_pair')
        response = self.client.post(url, {
            'username': username,
            'password': password
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data['access']

    def test_assign_roles_to_user(self):
        """Test assigning roles to a user."""
        # Get access token for admin user
        token = self.get_token(username="admin_user", password="adminpass")
        print("Admin User:", self.admin_user.is_staff)
        print("Token:", token) 
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        print(self.client.defaults) 
        # Endpoint and data
        url = reverse('user-assign-roles', kwargs={'pk': self.role_user.id})
        print(url)
        print("Users in DB:", User.objects.all()) 
        data = {"roles": [self.doctor_role.id]}
        print("Role User ID:", self.role_user.id)
        print("Resolved URL:", reverse('user-assign-roles', kwargs={'pk': self.role_user.id}))
        print(data)
        # Post request to assign roles
        response = self.client.post(url, data, format='json')
        print("Response Status Code:", response.status_code)
        print("Response Data:", response.data)

        self.role_user.refresh_from_db()

        print("Role's Group:", self.doctor_role.group)  # Should print the Doctor group
        print("User Groups After API Call:", list(self.role_user.groups.all()))  # Verify assignment
     
        # Assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.doctor_role.group, self.role_user.groups.all())
