 
from __future__ import annotations

import base64
import os
import struct
from dataclasses import dataclass
from typing import Protocol

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
from django.conf import settings


class EncryptionError(Exception):
    """Raised on any encryption/decryption failure. Never leak details to API clients."""

@dataclass(frozen=True)
class EncryptedPayload:
     
    wrapped_dek: bytes       
    nonce: bytes             
    ciphertext: bytes       
    key_id: str              

    def to_storage_string(self) -> str:
         
        blob = (
            struct.pack(">H", len(self.key_id.encode()))
            + self.key_id.encode()
            + struct.pack(">H", len(self.wrapped_dek))
            + self.wrapped_dek
            + struct.pack(">H", len(self.nonce))
            + self.nonce
            + self.ciphertext
        )
        return base64.b64encode(blob).decode("ascii")

    @classmethod
    def from_storage_string(cls, s: str) -> "EncryptedPayload":
        blob = base64.b64decode(s.encode("ascii"))
        pos = 0

        def read(n):
            nonlocal pos
            val = blob[pos:pos + n]
            pos += n
            return val

        key_id_len = struct.unpack(">H", read(2))[0]
        key_id = read(key_id_len).decode()
        dek_len = struct.unpack(">H", read(2))[0]
        wrapped_dek = read(dek_len)
        nonce_len = struct.unpack(">H", read(2))[0]
        nonce = read(nonce_len)
        ciphertext = blob[pos:]

        return cls(wrapped_dek=wrapped_dek, nonce=nonce, ciphertext=ciphertext, key_id=key_id)


class KMSClient(Protocol):
     

    def generate_data_key(self) -> tuple[bytes, bytes, str]:
         
        ...

    def decrypt_data_key(self, wrapped_dek: bytes, key_id: str) -> bytes:
         
        ...


class AWSKMSClient:
     

    def __init__(self, key_arn: str, region: str):
        import boto3  # imported lazily so dev environments don't need boto3 installed
        self._client = boto3.client("kms", region_name=region)
        self._key_arn = key_arn

    def generate_data_key(self) -> tuple[bytes, bytes, str]:
        resp = self._client.generate_data_key(KeyId=self._key_arn, KeySpec="AES_256")
        return resp["Plaintext"], resp["CiphertextBlob"], self._key_arn

    def decrypt_data_key(self, wrapped_dek: bytes, key_id: str) -> bytes:
        try:
            resp = self._client.decrypt(CiphertextBlob=wrapped_dek, KeyId=key_id)
            return resp["Plaintext"]
        except Exception as exc:  # noqa: BLE001 — intentionally broad, re-raised as domain error
            raise EncryptionError("Unable to unwrap data key") from exc


class LocalDevKMSClient:
     

    def __init__(self, master_key_b64: str):
        self._master_key = base64.b64decode(master_key_b64)
        if len(self._master_key) != 32:
            raise EncryptionError("Dev KMS master key must be 32 bytes (AES-256)")
        self._aesgcm = AESGCM(self._master_key)
        self._key_id = "local-dev-key-v1"

    def generate_data_key(self) -> tuple[bytes, bytes, str]:
        dek = os.urandom(32)
        nonce = os.urandom(12)
        wrapped = nonce + self._aesgcm.encrypt(nonce, dek, None)
        return dek, wrapped, self._key_id

    def decrypt_data_key(self, wrapped_dek: bytes, key_id: str) -> bytes:
        if key_id != self._key_id:
            raise EncryptionError("Unknown dev key id")
        nonce, ct = wrapped_dek[:12], wrapped_dek[12:]
        try:
            return self._aesgcm.decrypt(nonce, ct, None)
        except InvalidTag as exc:
            raise EncryptionError("Data key unwrap failed (tampered or wrong key)") from exc


def get_kms_client() -> KMSClient:
    backend = getattr(settings, "KMS_BACKEND", "local")

    if backend == "aws":
        return AWSKMSClient(
            key_arn=settings.KMS_KEY_ARN,
            region=settings.KMS_REGION,
        )
    if backend == "local":
        if not settings.DEBUG:
            raise RuntimeError(
                "Refusing to start: KMS_BACKEND=local is a dev-only stub and must not "
                "run with DEBUG=False. Configure a real KMS backend for production."
            )
        return LocalDevKMSClient(settings.LOCAL_DEV_MASTER_KEY)

    raise RuntimeError(f"Unknown KMS_BACKEND: {backend}")


class EnvelopeEncryptor:
    

    def __init__(self, kms_client: KMSClient | None = None):
        self._kms = kms_client or get_kms_client()

    def encrypt(self, plaintext: bytes, *, aad: bytes | None = None) -> EncryptedPayload:
         
        dek, wrapped_dek, key_id = self._kms.generate_data_key()
        try:
            nonce = os.urandom(12)   
            aesgcm = AESGCM(dek)
            ciphertext = aesgcm.encrypt(nonce, plaintext, aad)
            return EncryptedPayload(wrapped_dek=wrapped_dek, nonce=nonce, ciphertext=ciphertext, key_id=key_id)
        finally:
             
            dek = b"\x00" * len(dek)
            del dek

    def decrypt(self, payload: EncryptedPayload, *, aad: bytes | None = None) -> bytes:
        dek = self._kms.decrypt_data_key(payload.wrapped_dek, payload.key_id)
        try:
            aesgcm = AESGCM(dek)
            try:
                return aesgcm.decrypt(payload.nonce, payload.ciphertext, aad)
            except InvalidTag as exc:
                raise EncryptionError(
                    "Decryption failed: ciphertext tampered, wrong AAD, or wrong key"
                ) from exc
        finally:
            dek = b"\x00" * len(dek)
            del dek


def hash_share_token(raw_token: str) -> str:
     
    import hmac
    import hashlib

    pepper = settings.SHARE_TOKEN_PEPPER.encode()
    return hmac.new(pepper, raw_token.encode(), hashlib.sha256).hexdigest()