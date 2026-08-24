

from celery import shared_task
from django.utils import timezone
from apps.ocr.services.data_extractor import extract_structured_data
from common.supabase_client import get_supabase_client
from common.storage.supabase_storage import SupabaseStorage
from .models import ExtractedData, OCRJob, OCRResult
from .services.ocr_engine import perform_ocr
from .services.classifier import classify_document   # new import
import logging

logger = logging.getLogger(__name__)
@shared_task
def extract_structured_data_task(document_id: str):
 
    try:
        # Get OCR result
        ocr_result = OCRResult.objects.get(document_id=document_id)
        text = ocr_result.extracted_text
        if not text:
            logger.warning(f"No OCR text for document {document_id}")
            return

        # Classify document (if not already classified)
        doc_type = classify_document(text)

        # Extract data
        extracted = extract_structured_data(text, doc_type, use_ai=True)

        # Save extracted data
        data, created = ExtractedData.objects.update_or_create(
            document_id=document_id,
            defaults={
                'doc_type': doc_type,
                'data': extracted,
                'confidence': ocr_result.confidence,
                'updated_at': timezone.now(),
            }
        )

        logger.info(f"Extracted data for document {document_id}: {extracted}")
        return data.id

    except Exception as e:
        logger.exception(f"Data extraction failed for document {document_id}")
        raise
@shared_task
def run_ocr_job(job_id: str, document_id: str, user_id: str):
    job = OCRJob.objects.get(id=job_id)
    try:
        job.status = 'running'
        job.save(update_fields=['status'])

        supabase = get_supabase_client()
        pages_resp = supabase.table('pages')\
            .select('image_storage_path, page_number')\
            .eq('document_id', document_id)\
            .order('page_number')\
            .execute()

        if not pages_resp.data:
            raise ValueError("No pages found for this document")

        storage = SupabaseStorage('scans')
        page_texts = []
        total_confidence = 0.0
        page_count = len(pages_resp.data)
        detected_language = 'unknown'

        for page_data in pages_resp.data:
            storage_path = page_data['image_storage_path']
            if storage_path.startswith('scans/'):
                storage_path = storage_path[6:]

            page_num = page_data['page_number']
            try:
                image_bytes = storage.download(
                    owner_id=user_id,
                    document_id=document_id,
                    storage_path=storage_path
                )
                text, lang, conf = perform_ocr(image_bytes)
                page_texts.append(f"--- Page {page_num} ---\n{text}")
                total_confidence += conf
                if lang != 'unknown' and detected_language == 'unknown':
                    detected_language = lang
            except Exception as e:
                logger.error(f"Page {page_num} OCR failed: {e}")
                page_texts.append(f"--- Page {page_num} ---\n[OCR failed: {e}]")

        combined_text = "\n\n".join(page_texts)
        avg_confidence = total_confidence / page_count if page_count > 0 else 0.0

        
        doc_type = classify_document(combined_text)
        logger.info(f"Classified document {document_id} as: {doc_type}")

        # Save OCR result
        result, _ = OCRResult.objects.get_or_create(document_id=document_id)
        result.extracted_text = combined_text
        result.detected_language = detected_language if detected_language != 'unknown' else 'ne+en'
        result.confidence = avg_confidence
        result.save()

        # Update document with classification and status
        supabase.table('documents').update({
            'doc_type': doc_type,
            'ocr_status': 'done'
        }).eq('id', document_id).execute()

        job.status = 'done'
        job.error_message = None

    except Exception as e:
        job.status = 'failed'
        job.error_message = str(e)
        logger.exception("OCR job failed")

    finally:
        job.completed_at = timezone.now()
        job.save(update_fields=['status', 'error_message', 'completed_at'])