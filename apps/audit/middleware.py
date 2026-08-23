 
import re
from apps.audit.services import log_document_access

_SENSITIVE_PATH_PATTERNS = [
    re.compile(r"^/api/v1/ocr/status/(?P<document_id>[0-9a-fA-F-]{36})/$"),
    re.compile(r"^/api/v1/documents/(?P<document_id>[0-9a-fA-F-]{36})/download/$"),
    re.compile(r"^/api/v1/expense/(?P<document_id>[0-9a-fA-F-]{36})/$"),
]

class DocumentAccessAuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if response.status_code == 200 and hasattr(request, "user") and request.user:
            for pattern in _SENSITIVE_PATH_PATTERNS:
                match = pattern.match(request.path)
                if match:
                    log_document_access(
                        event="viewed",
                        user_id=str(getattr(request.user, "id", "unknown")),
                        document_id=match.group("document_id"),
                        ip=self._client_ip(request),
                        user_agent=request.META.get("HTTP_USER_AGENT", ""),
                    )
                    break
        return response

    @staticmethod
    def _client_ip(request) -> str:
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff and getattr(request, "_trusted_proxy", False):
            return xff.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")