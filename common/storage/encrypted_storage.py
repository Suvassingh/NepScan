from __future__ import annotations

import logging
import uuid

from common.encryption import (
    EncryptedPayload,
    EncryptionError,
    EnvelopeEncryptor,
)
from common.supabase_client import get_supabase_client
from apps.billing.models import StorageEncryptionMetadata


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

        # Upload only the ciphertext. Do NOT rely on Supabase file_options
        # for anything that needs to survive — it does not support
        # arbitrary custom object metadata the way S3 does.
        self._client.storage.from_(self._bucket).upload(
            path=storage_path,
            file=payload.ciphertext,
            file_options={
                "content-type": "application/octet-stream",
            },
        )

        # Persist the encryption metadata ourselves, in the database.
        try:
            StorageEncryptionMetadata.objects.create(
                storage_path=storage_path,
                wrapped_dek=payload.wrapped_dek,
                nonce=payload.nonce,
                key_id=payload.key_id,
                original_content_type=content_type,
            )
        except Exception as exc:
            # If we can't persist the metadata, the uploaded ciphertext is
            # unrecoverable — clean it up rather than leaving an orphaned,
            # undecryptable blob in storage.
            try:
                self._client.storage.from_(self._bucket).remove([storage_path])
            except Exception:
                logger.error(
                    "Failed to roll back orphaned upload at %s after metadata "
                    "write failure",
                    storage_path,
                )
            raise EncryptionError(
                f"Failed to persist encryption metadata for {storage_path}"
            ) from exc

        return storage_path

    def download(
        self,
        *,
        owner_id: str,
        document_id: str,
        storage_path: str,
    ) -> bytes:
        # 1. Download the encrypted file bytes
        obj = self._client.storage.from_(self._bucket).download(storage_path)

        # 2. Look up encryption metadata from our own database
        try:
            meta = StorageEncryptionMetadata.objects.get(storage_path=storage_path)
        except StorageEncryptionMetadata.DoesNotExist as exc:
            raise EncryptionError(
                f"Missing encryption metadata (wrapped_dek or nonce) for {storage_path}"
            ) from exc

        wrapped_dek = bytes(meta.wrapped_dek)
        nonce = bytes(meta.nonce)
        key_id = meta.key_id

        if not wrapped_dek or not nonce:
            raise EncryptionError(
                f"Missing encryption metadata (wrapped_dek or nonce) for {storage_path}"
            )

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
        StorageEncryptionMetadata.objects.filter(storage_path=storage_path).delete()