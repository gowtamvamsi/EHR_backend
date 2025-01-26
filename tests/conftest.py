import pytest
import os
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from users.models import User, Role

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def create_user():
    return User.objects.create_user(
        username='testuser',
        password='testpass123',
        email='test@example.com',
        first_name='Test',
        last_name='User',
        role=Role.RoleType.PATIENT,
        phone_number='+911234567890'
    )

@pytest.fixture
def authenticated_client(api_client, create_user):
    api_client.force_authenticate(user=create_user)
    return api_client

@pytest.fixture
def doctor_user():
    return User.objects.create_user(
        username='doctor',
        password='testpass123',
        email='doctor@example.com',
        first_name='Doctor',
        last_name='Test',
        role=Role.RoleType.DOCTOR,
        phone_number='+911234567891'
    )

@pytest.fixture
def test_image():
    file_path = os.path.join(os.path.dirname(__file__), 'test_files/test_image.jpg')
    with open(file_path, 'rb') as f:
        return SimpleUploadedFile(
            'test_image.jpg',
            f.read(),
            content_type='image/jpeg'
        )