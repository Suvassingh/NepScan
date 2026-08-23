import hmac
import hashlib
from django.conf import settings

def verify_webhook(request) -> bool:
    signature = request.headers.get('Authorization', '')
    if not signature.startswith('Bearer '):
        return False
    token = signature.split(' ')[1]
     
    expected = hmac.new(settings.REVENUECAT_WEBHOOK_SECRET.encode(), request.body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(token, expected)