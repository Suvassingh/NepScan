import uuid
from django.db import models
from common.fields import EncryptedTextField, DecryptOnAccessMixin

class OCRJob(models.Model):
    JOB_TYPES = [
        ('ocr', 'OCR'),
        ('pdf_compress', 'PDF Compress'),
        ('pdf_merge', 'PDF Merge'),
        ('ai_summary', 'AI Summary'),
        ('expense_extract', 'Expense Extract'),
    ]
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('running', 'Running'),
        ('done', 'Done'),
        ('failed', 'Failed'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document_id = models.UUIDField(db_index=True)
    job_type = models.CharField(max_length=20, choices=JOB_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'ocr_jobs'
        managed = False

class OCRResult(DecryptOnAccessMixin, models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document_id = models.UUIDField(unique=True, db_index=True)
    extracted_text_encrypted = EncryptedTextField(db_column='extracted_text', aad_field='document_id')
    detected_language = models.CharField(max_length=20, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    ai_summary = models.TextField(null=True, blank=True)  # optionally encrypted
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ocr_results'
        managed = False

    @property
    def extracted_text(self):
        return self._decrypt_field('extracted_text_encrypted', 'document_id')

    @extracted_text.setter
    def extracted_text(self, value):
        self.extracted_text_encrypted = value
        
class ExtractedData(models.Model):
     
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document_id = models.UUIDField(unique=True, db_index=True)
    doc_type = models.CharField(max_length=50, blank=True)  # receipt, invoice, id_card, etc.
    data = models.JSONField(default=dict)  # stores all extracted fields as JSON
    confidence = models.FloatField(null=True, blank=True)  # overall confidence score
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'extracted_data'