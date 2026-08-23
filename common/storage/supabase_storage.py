import logging
from common.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

class SupabaseStorage:
    def __init__(self, bucket: str):
        self._client = get_supabase_client()
        self._bucket = bucket

    def download(self, *, owner_id: str, document_id: str, storage_path: str) -> bytes:
         
        original_path = storage_path
        if storage_path.lower().startswith(self._bucket.lower() + '/'):
            storage_path = storage_path[len(self._bucket) + 1:]
         
        if storage_path.startswith('/'):
            storage_path = storage_path[1:]

        logger.info(f"Downloading from bucket '{self._bucket}' with path: {storage_path} (original: {original_path})")

        try:
            return self._client.storage.from_(self._bucket).download(storage_path)
        except Exception as e:
            logger.error(f"Failed to download {storage_path} from bucket {self._bucket}: {e}")
             
            if storage_path != original_path:
                try:
                    logger.info(f"Retrying with original path: {original_path}")
                    return self._client.storage.from_(self._bucket).download(original_path)
                except Exception as e2:
                    logger.error(f"Fallback also failed: {e2}")
                    raise Exception(f"File not found: {original_path} in bucket {self._bucket}") from e2
            raise Exception(f"File not found: {storage_path} in bucket {self._bucket}") from e

    def upload(self, *, owner_id: str, document_id: str, file_bytes: bytes, content_type: str) -> str:
         
        raise NotImplementedError("Upload not implemented in SupabaseStorage; use EncryptedSupabaseStorage")