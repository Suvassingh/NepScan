 
from __future__ import annotations

import jwt
from jwt import PyJWKClient
from django.conf import settings
from django.core.cache import cache
from rest_framework import authentication, exceptions
from apps.audit.services import log_auth_event


class SupabaseUser:
     
    is_authenticated = True

    def __init__(self, claims: dict):
        self.id = claims["sub"]
        self.email = claims.get("email")
        self.role = claims.get("role", "authenticated")
        self.claims = claims

    def __str__(self):
        return self.id
    
    @property
    def pk(self):
        return self.id   

    def __str__(self):
        return self.id


class SupabaseJWTAuthentication(authentication.BaseAuthentication):
    ALGORITHMS = ["ES256", "RS256"]   

    def __init__(self):
        self._jwk_client = PyJWKClient(settings.SUPABASE_JWKS_URL, cache_keys=True)

    def authenticate(self, request):
        auth_header = authentication.get_authorization_header(request).decode("utf-8")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.removeprefix("Bearer ").strip()
        client_ip = request.META.get("REMOTE_ADDR", "unknown")

        try:
            signing_key = self._jwk_client.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=self.ALGORITHMS,
                audience=settings.SUPABASE_JWT_AUDIENCE,
                issuer=settings.SUPABASE_JWT_ISSUER,
                options={
                    "require": ["exp", "iat", "sub", "aud", "iss"],
                    "verify_exp": True,
                    "verify_iat": True,
                },
                leeway=10,
            )
        except jwt.ExpiredSignatureError:
            log_auth_event(event="token_expired", ip=client_ip)
            raise exceptions.AuthenticationFailed("Token expired")
        except jwt.InvalidTokenError as exc:
            log_auth_event(event="token_invalid", ip=client_ip, detail=str(exc))
            raise exceptions.AuthenticationFailed("Invalid authentication token")

        self._check_not_revoked(claims, client_ip)

        user = SupabaseUser(claims)
        log_auth_event(event="authenticated", ip=client_ip, user_id=user.id)
        return (user, token)

    def _check_not_revoked(self, claims: dict, client_ip: str) -> None:
        jti = claims.get("jti") or claims["sub"]
        if cache.get(f"revoked_token:{jti}"):
            log_auth_event(event="revoked_token_reuse_attempt", ip=client_ip, user_id=claims["sub"])
            raise exceptions.AuthenticationFailed("Token has been revoked")

    def authenticate_header(self, request):
        return "Bearer"


def revoke_token(jti_or_sub: str, ttl_seconds: int = 86400) -> None:
     
    cache.set(f"revoked_token:{jti_or_sub}", True, timeout=ttl_seconds)
    