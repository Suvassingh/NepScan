import uuid
from django.db import models

class Annotation(models.Model):
     
    TYPE_CHOICES = [
        ('freehand', 'Freehand Drawing'),
        ('text', 'Text Label'),
        ('rectangle', 'Rectangle'),
        ('circle', 'Circle'),
        ('arrow', 'Arrow'),
        ('highlight', 'Highlight'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document_id = models.UUIDField(db_index=True)
    page_number = models.IntegerField(default=1)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    data = models.JSONField(default=dict)  
    user_id = models.UUIDField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'annotations'