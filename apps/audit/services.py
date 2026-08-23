 
from apps.audit.models import AuditLogEntry

def log_auth_event(*, event: str, ip: str, user_id: str | None = None, detail: str | None = None):
    AuditLogEntry.record(
        event_type=f"auth.{event}",
        actor_id=user_id,
        ip_address=ip if ip != "unknown" else None,
        detail={"message": detail} if detail else None,
    )

def log_document_access(*, event: str, user_id: str, document_id: str, ip: str, user_agent: str = ""):
    AuditLogEntry.record(
        event_type=f"document.{event}",
        actor_id=user_id,
        target_type="document",
        target_id=document_id,
        ip_address=ip,
        user_agent=user_agent[:500],
    )

def log_admin_event(*, event: str, admin_id: str, ip: str, detail: dict | None = None):
    AuditLogEntry.record(
        event_type=f"admin.{event}",
        actor_id=admin_id,
        actor_role="staff",
        ip_address=ip,
        detail=detail,
    )