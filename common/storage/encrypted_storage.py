
from __future__ import annotations

import base64
import logging
import uuid

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

        storage_path = (
            f"{owner_id}/{document_id}/{uuid.uuid4().hex}.enc"
        )

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

    def download(
        self,
        *,
        owner_id: str,
        document_id: str,
        storage_path: str,
    ) -> bytes:
        # 1. Download the file bytes (this proves the file exists)
        obj = self._client.storage.from_(self._bucket).download(
            storage_path
        )

        # 2. Get metadata by listing the parent directory.
        # Split the path to get directory and filename.
        if "/" in storage_path:
            dir_path = storage_path.rsplit("/", 1)[0] + "/"
            filename = storage_path.rsplit("/", 1)[1]
        else:
            dir_path = ""
            filename = storage_path

        # List the directory.
        file_list = self._client.storage.from_(self._bucket).list(
            dir_path
        )

        meta = {}

        for entry in file_list:
            if entry["name"] == filename:
                meta = entry.get("metadata", {})
                break

        if not meta:
            # If we still can't find metadata, raise a descriptive error.
            raise EncryptionError(
                f"Could not retrieve metadata for {storage_path}"
            )

        wrapped_dek_str = meta.get("x-amz-meta-wrapped-dek")
        nonce_str = meta.get("x-amz-meta-nonce")
        key_id = meta.get("x-amz-meta-key-id")

        if not wrapped_dek_str or not nonce_str:
            raise EncryptionError(
                "Missing encryption metadata (wrapped_dek or nonce)"
            )

        wrapped_dek = None
        nonce = None

        # Try hex.
        try:
            wrapped_dek = bytes.fromhex(wrapped_dek_str)
            nonce = bytes.fromhex(nonce_str)
        except ValueError:
            pass

        # Try base64.
        if wrapped_dek is None:
            try:
                wrapped_dek = base64.b64decode(wrapped_dek_str)
                nonce = base64.b64decode(nonce_str)
            except Exception as e:
                logger.error(f"Failed to decode metadata: {e}")
                raise EncryptionError(
                    "Unable to decode encryption metadata"
                ) from e

        payload = EncryptedPayload(
            wrapped_dek=wrapped_dek,
            nonce=nonce,
            ciphertext=obj,
            key_id=key_id,
        )

        aad = f"{owner_id}:{document_id}".encode()

        return self._encryptor.decrypt(
            payload,
            aad=aad,
        )

    def delete(self, storage_path: str) -> None:
        self._client.storage.from_(self._bucket).remove(
            [storage_path]
        )
