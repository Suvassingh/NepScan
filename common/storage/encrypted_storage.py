from __future__ import annotations

import base64
import logging
import uuid

import requests  # ✅ needed for HEAD request
from django.conf import settings

from common.encryption import (
    EncryptedPayload,
    EncryptionError,
    EnvelopeEncryptor,
)
from common.supabase_client import get_supabase_client


logger = logging.getLogger(__name__)


class EncryptedSupabaseStorage:
    def __init__(self, bucket: str):
        self._client = get_supabase_client()
        self._bucket = bucket
        self._encryptor = EnvelopeEncryptor()

    def upload(
        self,
        *,
        owner_id: str,
        document_id: str,
        file_bytes: bytes,
        content_type: str,
    ) -> str:
        aad = f"{owner_id}:{document_id}".encode()

        payload: EncryptedPayload = self._encryptor.encrypt(
            file_bytes,
            aad=aad,
        )

        storage_path = f"{owner_id}/{document_id}/{uuid.uuid4().hex}.enc"

        self._client.storage.from_(self._bucket).upload(
            path=storage_path,
            file=payload.ciphertext,
            file_options={
                "content-type": "application/octet-stream",
                "x-amz-meta-wrapped-dek": payload.wrapped_dek.hex(),
                "x-amz-meta-nonce": payload.nonce.hex(),
                "x-amz-meta-key-id": payload.key_id,
                "x-amz-meta-original-content-type": content_type,
            },
        )

        return storage_path

    def _get_metadata(self, storage_path: str) -> dict:
        """
        Retrieve object metadata using a HEAD request.
        Returns a dict containing the custom metadata keys (without the 'x-amz-meta-' prefix).
        """
        url = (
            f"{settings.SUPABASE_URL}/storage/v1/object/{self._bucket}/{storage_path}"
        )
        headers = {
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}"
        }

        try:
            response = requests.head(url, headers=headers, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise EncryptionError(
                f"Failed to retrieve metadata for {storage_path}: {e}"
            ) from e

        # Extract custom metadata
        meta = {}
        for key, value in response.headers.items():
            if key.lower().startswith("x-amz-meta-"):
                meta_key = key[11:]  # remove "x-amz-meta-"
                meta[meta_key] = value

        return meta

    def download(
        self,
        *,
        owner_id: str,
        document_id: str,
        storage_path: str,
    ) -> bytes:
        # 1. Download the encrypted file bytes
        obj = self._client.storage.from_(self._bucket).download(storage_path)

        # 2. Get encryption metadata via HEAD request
        meta = self._get_metadata(storage_path)

        wrapped_dek_str = meta.get("wrapped-dek")
        nonce_str = meta.get("nonce")
        key_id = meta.get("key-id")

        if not wrapped_dek_str or not nonce_str:
            raise EncryptionError(
                f"Missing encryption metadata (wrapped_dek or nonce) for {storage_path}"
            )

        # Decode from hex (preferred) or base64
        wrapped_dek = None
        nonce = None
        try:
            wrapped_dek = bytes.fromhex(wrapped_dek_str)
            nonce = bytes.fromhex(nonce_str)
        except ValueError:
            try:
                wrapped_dek = base64.b64decode(wrapped_dek_str)
                nonce = base64.b64decode(nonce_str)
            except Exception as e:
                logger.error(f"Failed to decode metadata: {e}")
                raise EncryptionError("Unable to decode encryption metadata") from e

        payload = EncryptedPayload(
            wrapped_dek=wrapped_dek,
            nonce=nonce,
            ciphertext=obj,
            key_id=key_id,
        )

        aad = f"{owner_id}:{document_id}".encode()
        return self._encryptor.decrypt(payload, aad=aad)

    def delete(self, storage_path: str) -> None:
        self._client.storage.from_(self._bucket).remove([storage_path])