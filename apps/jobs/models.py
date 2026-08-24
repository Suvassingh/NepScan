import uuid
from django.db import models

class Job(models.Model):
    JOB_TYPES = [
        ('ocr', 'OCR'),
        ('conversion', 'Conversion'),
        ('ai_summary', 'AI Summary'),
        ('expense_extract', 'Expense Extract'),
        ('pdf_compress', 'PDF Compress'),
         
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
    result = models.TextField(blank=True, null=True)          # store download URL or path
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'jobs'