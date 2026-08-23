
from abc import ABC, abstractmethod

class BaseStorage(ABC):
    @abstractmethod
    def upload(self, *, owner_id: str, document_id: str, file_bytes: bytes, content_type: str) -> str:
         
        pass

    @abstractmethod
    def download(self, *, owner_id: str, document_id: str, storage_path: str) -> bytes:
         
        pass

    @abstractmethod
    def delete(self, storage_path: str) -> None:
         
        pass