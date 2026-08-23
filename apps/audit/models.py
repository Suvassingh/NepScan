 
import hashlib
from django.db import models

class AuditLogEntry(models.Model):
    EVENT_CHOICES = [
        ("auth.authenticated", "Authenticated"),
        ("auth.token_invalid", "Invalid token presented"),
        ("auth.token_expired", "Expired token presented"),
        ("auth.revoked_token_reuse_attempt", "Revoked token reuse attempt"),
        ("document.viewed", "Document viewed"),
        ("document.downloaded", "Document downloaded"),
        ("document.decrypted", "Document content decrypted"),
        ("document.shared", "Document share created"),
        ("document.deleted", "Document deleted"),
        ("admin.accessed", "Admin panel accessed"),
        ("admin.data_export", "Admin exported data"),
        ("key.rotation", "Encryption key rotation performed"),
    ]

    id = models.BigAutoField(primary_key=True)
    event_type = models.CharField(max_length=64, choices=EVENT_CHOICES, db_index=True)
    actor_id = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    actor_role = models.CharField(max_length=32, default="unknown")
    target_type = models.CharField(max_length=64, null=True, blank=True)
    target_id = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    detail = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    previous_hash = models.CharField(max_length=64, blank=True, default="")
    entry_hash = models.CharField(max_length=64, editable=False)

    class Meta:
        db_table = "audit_log_entries"
        ordering = ["id"]

    def compute_hash(self) -> str:
        payload = "|".join([
            self.previous_hash,
            self.event_type,
            str(self.actor_id),
            str(self.target_id),
            str(self.ip_address),
            str(self.created_at),
        ])
        return hashlib.sha256(payload.encode()).hexdigest()

    def save(self, *args, **kwargs):
        if not self.pk:
            last = AuditLogEntry.objects.order_by("-id").first()
            self.previous_hash = last.entry_hash if last else ""
        super().save(*args, **kwargs)

    @classmethod
    def record(cls, **fields) -> "AuditLogEntry":
        entry = cls(**fields)
        entry.save()
        entry.entry_hash = entry.compute_hash()
        entry.save(update_fields=["entry_hash"])
        return entry

    @classmethod
    def verify_chain(cls, start_id: int = 1) -> tuple[bool, int | None]:
        prev_hash = ""
        for entry in cls.objects.filter(id__gte=start_id).order_by("id"):
            if entry.previous_hash != prev_hash:
                return False, entry.id
            if entry.entry_hash != entry.compute_hash():
                return False, entry.id
            prev_hash = entry.entry_hash
        return True, None