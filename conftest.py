import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user_data():
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpass123',
        'first_name': 'Test',
        'last_name': 'User',
        'role': 'PATIENT',
        'phone_number': '+911234567890'
    }

@pytest.fixture
def create_user(user_data):
    User = get_user_model()
    return User.objects.create_user(**user_data)