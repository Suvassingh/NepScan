 
from django.db import models

from common.encryption import EncryptedPayload, EnvelopeEncryptor, EncryptionError


class EncryptedTextField(models.TextField):
   

    def __init__(self, *args, aad_field: str | None = None, **kwargs):
        self.aad_field = aad_field
        
        kwargs.setdefault("db_index", False)
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.aad_field:
            kwargs["aad_field"] = self.aad_field
        return name, path, args, kwargs

    def _get_aad(self, model_instance) -> bytes | None:
        if not self.aad_field:
            return None
        value = getattr(model_instance, self.aad_field, None)
        return str(value).encode() if value is not None else None

    def pre_save(self, model_instance, add):
        raw_value = getattr(model_instance, self.attname)
        if raw_value is None:
            return None
        if raw_value == "":
            return ""

        encryptor = EnvelopeEncryptor()
        aad = self._get_aad(model_instance)
        payload = encryptor.encrypt(raw_value.encode("utf-8"), aad=aad)
        stored = payload.to_storage_string()

       
        setattr(model_instance, self.attname, raw_value)
        return stored

    def from_db_value(self, value, expression, connection):
        if value is None or value == "":
            return value
        try:
            payload = EncryptedPayload.from_storage_string(value)
        except Exception:
            
            raise EncryptionError("Stored value is not a valid encrypted payload")

        
        return payload.to_storage_string()   

class DecryptOnAccessMixin:
    
    def _decrypt_field(self, encrypted_attname: str, aad_field: str | None = None) -> str | None:
        raw = getattr(self, encrypted_attname)
        if raw in (None, ""):
            return raw

        from common.encryption import EncryptedPayload, EnvelopeEncryptor

        payload = EncryptedPayload.from_storage_string(raw)
        aad = str(getattr(self, aad_field)).encode() if aad_field else None
        plaintext = EnvelopeEncryptor().decrypt(payload, aad=aad)
        return plaintext.decode("utf-8")


 