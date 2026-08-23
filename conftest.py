import pytest
from django.test import Client
from rest_framework.test import APIClient
from django.core.cache import cache
from unittest.mock import patch

@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def auth_client(api_client):
    # Mock a valid Supabase JWT
    with patch('apps.authentication.backends.SupabaseJWTAuthentication.authenticate') as mock_auth:
        user = type('User', (), {'id': 'test-user-123', 'is_authenticated': True})()
        mock_auth.return_value = (user, 'fake-token')
        api_client.credentials(HTTP_AUTHORIZATION='Bearer fake-token')
        yield api_client