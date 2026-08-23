import uuid
from django.db import models

class Subscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner_id = models.UUIDField(unique=True, db_index=True)
    plan = models.CharField(max_length=20, default='free')
    status = models.CharField(max_length=20, default='active')
    current_period_end = models.DateTimeField(null=True, blank=True)
    provider = models.CharField(max_length=20, blank=True)

    class Meta:
        db_table = 'subscriptions'

class DocumentShare(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document_id = models.UUIDField(db_index=True)
    owner_id = models.UUIDField(db_index=True)
    shared_with_id = models.UUIDField(null=True, blank=True)
    organization_id = models.UUIDField(null=True, blank=True, db_index=True)
    permission = models.CharField(max_length=20, default='view')
    share_token = models.CharField(max_length=64, null=True, blank=True, unique=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'document_shares'
        managed = False   