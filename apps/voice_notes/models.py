import uuid
from django.db import models

class VoiceNote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document_id = models.UUIDField(db_index=True)
    owner_id = models.UUIDField(db_index=True)
    storage_path = models.TextField()
    transcript = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'voice_notes'