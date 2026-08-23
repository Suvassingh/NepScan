 
from __future__ import annotations

import uuid
import base64
import logging
from common.encryption import EncryptedPayload, EnvelopeEncryptor, EncryptionError
from common.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

class EncryptedSupabaseStorage:
    def __init__(self, bucket: str):
        self._client = get_supabase_client()
        self._bucket = bucket
        self._encryptor = EnvelopeEncryptor()

    def upload(self, *, owner_id: str, document_id: str, file_bytes: bytes, content_type: str) -> str:
        aad = f"{owner_id}:{document_id}".encode()
        payload: EncryptedPayload = self._encryptor.encrypt(file_bytes, aad=aad)

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

    def download(self, *, owner_id: str, document_id: str, storage_path: str) -> bytes:
        obj = self._client.storage.from_(self._bucket).download(storage_path)
        
         
        file_list = self._client.storage.from_(self._bucket).list(storage_path)
        if not file_list:
            raise EncryptionError(f"File not found: {storage_path}")
        meta = file_list[0].get('metadata', {})

        logger.info(f"Downloading file: {storage_path}, metadata keys: {list(meta.keys())}")

        wrapped_dek_str = meta.get("x-amz-meta-wrapped-dek")
        nonce_str = meta.get("x-amz-meta-nonce")
        key_id = meta.get("x-amz-meta-key-id")

        if not wrapped_dek_str or not nonce_str:
            raise EncryptionError("Missing encryption metadata (wrapped_dek or nonce)")

        wrapped_dek = None
        nonce = None

         
        try:
            wrapped_dek = bytes.fromhex(wrapped_dek_str)
            nonce = bytes.fromhex(nonce_str)
            logger.info("Decoded metadata as hex")
        except ValueError:
            pass

        
        if wrapped_dek is None:
            try:
                wrapped_dek = base64.b64decode(wrapped_dek_str)
                nonce = base64.b64decode(nonce_str)
                logger.info("Decoded metadata as base64")
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