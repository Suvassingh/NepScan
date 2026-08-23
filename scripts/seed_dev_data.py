"""
Seed development data into Supabase or local DB.

Run with:
    python manage.py runscript seed_dev_data
(if using django-extensions) or directly: python scripts/seed_dev_data.py
"""
import os
import sys
import uuid
from datetime import datetime, timedelta
from faker import Faker
from django.conf import settings

# Adjust path to allow imports from apps
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
import django
django.setup()

from apps.ocr.models import OCRJob, OCRResult
from apps.audit.models import AuditLogEntry
from common.supabase_client import get_supabase_client
from common.encryption import EnvelopeEncryptor

fake = Faker()

def create_test_document():
    # Simulate creating a document in Supabase – we'll insert a row in documents table
    supabase = get_supabase_client()
    doc_id = str(uuid.uuid4())
    owner_id = 'test-user-123'  # replace with actual Supabase user ID
    data = {
        'id': doc_id,
        'owner_id': owner_id,
        'title': fake.sentence(nb_words=4),
        'doc_type': fake.random_element(elements=('document', 'receipt', 'id_card', 'book')),
        'page_count': fake.random_int(min=1, max=5),
        'file_size_bytes': fake.random_int(min=1024, max=10*1024*1024),
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
    }
    supabase.table('documents').insert(data).execute()
    return doc_id, owner_id

def create_ocr_job_and_result(doc_id, owner_id):
    # Create an OCRJob row
    job = OCRJob.objects.create(
        document_id=doc_id,
        job_type='ocr',
        status='done',
        completed_at=datetime.now()
    )
    # Create OCRResult with encrypted text
    encryptor = EnvelopeEncryptor()
    plaintext = fake.paragraph(nb_sentences=10)
    payload = encryptor.encrypt(plaintext.encode('utf-8'), aad=doc_id.encode())
    result = OCRResult.objects.create(
        document_id=doc_id,
        detected_language='ne+en',
        confidence=0.98,
        ai_summary=fake.sentence(),
        extracted_text=payload.to_storage_string()  # Encrypted field will handle decode
    )
    # Also create an audit entry
    AuditLogEntry.record(
        event_type='document.viewed',
        actor_id=owner_id,
        target_type='document',
        target_id=doc_id,
        ip_address='127.0.0.1',
        detail={'source': 'seed_script'}
    )
    print(f"Created document {doc_id} with OCR result")

def main():
    print("Seeding development data...")
    for _ in range(5):
        doc_id, owner_id = create_test_document()
        create_ocr_job_and_result(doc_id, owner_id)
    print("Seeding complete.")

if __name__ == '__main__':
    main()