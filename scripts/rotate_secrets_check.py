"""
Check and optionally rotate encryption keys and share token pepper.

Run as a cron job or manual admin task.
"""
import os
import sys
from django.conf import settings
from common.encryption import get_kms_client, EncryptionError

def check_kms():
    """Verify KMS is reachable and can generate/decrypt a test key."""
    try:
        client = get_kms_client()
        dek, wrapped, key_id = client.generate_data_key()
        decrypted = client.decrypt_data_key(wrapped, key_id)
        if dek != decrypted:
            raise RuntimeError("KMS test failed: decrypted DEK mismatch")
        print("KMS health check passed.")
    except Exception as e:
        print(f"KMS check failed: {e}")
        raise

def check_pepper():
    """Ensure SHARE_TOKEN_PEPPER is set and strong."""
    pepper = settings.SHARE_TOKEN_PEPPER
    if len(pepper) < 32:
        print("WARNING: SHARE_TOKEN_PEPPER is too short (<32 chars). Consider rotating.")
    else:
        print("Pepper strength OK.")

def main():
    print("Running security rotation checks...")
    check_kms()
    check_pepper()
    # Additional checks: audit log chain verification
    from apps.audit.models import AuditLogEntry
    valid, broken_id = AuditLogEntry.verify_chain()
    if not valid:
        print(f"Audit log chain broken at entry {broken_id}!")
        # Optionally trigger alert
    else:
        print("Audit log chain intact.")
    print("All checks completed.")

if __name__ == '__main__':
    main()