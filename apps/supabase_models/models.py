import uuid
from django.db import models

class Profile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    full_name = models.TextField(blank=True, null=True)
    avatar_url = models.TextField(blank=True, null=True)
    preferred_ocr_lang = models.CharField(max_length=20, default='ne+en')
    storage_used_bytes = models.BigIntegerField(default=0)
    plan = models.CharField(max_length=20, default='free')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'profiles'

class Folder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    owner_id = models.UUIDField(db_index=True)
    name = models.TextField()
    color = models.CharField(max_length=7, default='#4CFFB5')
    parent_folder_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'folders'

class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    owner_id = models.UUIDField(db_index=True)
    folder_id = models.UUIDField(null=True, blank=True)
    title = models.TextField(default='Untitled scan')
    doc_type = models.CharField(max_length=20, default='document')
    page_count = models.IntegerField(default=1)
    file_size_bytes = models.BigIntegerField(default=0)
    original_storage_path = models.TextField(blank=True, null=True)
    pdf_storage_path = models.TextField(blank=True, null=True)
    is_searchable = models.BooleanField(default=False)
    is_password_protected = models.BooleanField(default=False)
    ocr_status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'documents'

class Page(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    document_id = models.UUIDField(db_index=True)
    page_number = models.IntegerField()
    image_storage_path = models.TextField()
    filter_applied = models.CharField(max_length=20, default='original')
    brightness = models.IntegerField(default=0)
    contrast = models.IntegerField(default=0)
    rotation = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = 'pages'

class Tag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    owner_id = models.UUIDField(db_index=True)
    name = models.TextField()

    class Meta:
        managed = False
        db_table = 'tags'

class DocumentTag(models.Model):
    document_id = models.UUIDField()
    tag_id = models.UUIDField()

    class Meta:
        managed = False
        db_table = 'document_tags'
        unique_together = (('document_id', 'tag_id'),)

class OCRResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    document_id = models.UUIDField(unique=True, db_index=True)
    extracted_text = models.TextField(blank=True, null=True)  
    detected_language = models.TextField(blank=True, null=True)
    confidence = models.FloatField(blank=True, null=True)
    ai_summary = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'ocr_results'

class ExpenseData(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    document_id = models.UUIDField(unique=True, db_index=True)
    vendor = models.TextField(blank=True, null=True)
    expense_date = models.DateField(blank=True, null=True)
    category = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    currency = models.CharField(max_length=3, default='NPR')

    class Meta:
        managed = False
        db_table = 'expense_data'

class DocumentShare(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    document_id = models.UUIDField(db_index=True)
    owner_id = models.UUIDField(db_index=True)
    shared_with_id = models.UUIDField(null=True, blank=True)
    permission = models.CharField(max_length=10, default='view')
    share_token = models.TextField(unique=True, blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'document_shares'

class Subscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    owner_id = models.UUIDField(unique=True, db_index=True)
    plan = models.CharField(max_length=20, default='free')
    status = models.CharField(max_length=20, default='active')
    current_period_end = models.DateTimeField(blank=True, null=True)
    provider = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'subscriptions'