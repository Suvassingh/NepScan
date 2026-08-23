import pytest
from django.test import RequestFactory
from rest_framework.exceptions import AuthenticationFailed
from apps.authentication.backends import SupabaseJWTAuthentication, revoke_token
from unittest.mock import patch, MagicMock

@pytest.fixture
def auth_backend():
    return SupabaseJWTAuthentication()

def test_authenticate_missing_header(auth_backend):
    request = RequestFactory().get('/')
    result = auth_backend.authenticate(request)
    assert result is None

def test_authenticate_invalid_header(auth_backend):
    request = RequestFactory().get('/', HTTP_AUTHORIZATION='Basic abc')
    result = auth_backend.authenticate(request)
    assert result is None

def test_authenticate_expired_token(auth_backend):
    with patch('jwt.decode') as mock_decode:
        mock_decode.side_effect = jwt.ExpiredSignatureError
        request = RequestFactory().get('/', HTTP_AUTHORIZATION='Bearer eyJ...')
        with pytest.raises(AuthenticationFailed, match='Token expired'):
            auth_backend.authenticate(request)

def test_authenticate_invalid_token(auth_backend):
    with patch('jwt.decode') as mock_decode:
        mock_decode.side_effect = jwt.InvalidTokenError
        request = RequestFactory().get('/', HTTP_AUTHORIZATION='Bearer eyJ...')
        with pytest.raises(AuthenticationFailed, match='Invalid authentication token'):
            auth_backend.authenticate(request)

def test_authenticate_revoked_token(auth_backend):
    with patch('jwt.decode') as mock_decode:
        mock_decode.return_value = {'sub': 'user123', 'jti': 'jti123'}
        # Set cache to simulate revocation
        from django.core.cache import cache
        cache.set('revoked_token:jti123', True)
        request = RequestFactory().get('/', HTTP_AUTHORIZATION='Bearer eyJ...')
        with pytest.raises(AuthenticationFailed, match='Token has been revoked'):
            auth_backend.authenticate(request)

def test_revoke_token():
    revoke_token('jti123', ttl_seconds=60)
    from django.core.cache import cache
    assert cache.get('revoked_token:jti123') is True