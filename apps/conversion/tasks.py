from celery import shared_task
from django.utils import timezone
from apps.jobs.models import Job
from common.supabase_client import get_supabase_client
from common.storage.encrypted_storage import EncryptedSupabaseStorage
from common.storage.supabase_storage import SupabaseStorage
from apps.pdf_tools.services.pdf_compiler import merge_images_to_pdf
from .services.format_converter import (
    pdf_to_docx, pdf_to_long_image, pdf_to_long_image_jpg, pdf_to_pptx, pdf_to_xlsx, pdf_to_csv, pdf_to_txt, pdf_to_jpg,
    pdf_to_png, pdf_to_webp
)
import uuid
import logging
from .services.format_converter import pdf_to_pptx

logger = logging.getLogger(__name__)

@shared_task
def convert_document(job_id: str, document_id: str, target_format: str, user_id: str):
    job = Job.objects.get(id=job_id)
    try:
        job.status = 'running'
        job.save(update_fields=['status'])

        supabase = get_supabase_client()

        # Get document info
        doc_resp = supabase.table('documents').select('pdf_storage_path').eq('id', document_id).execute()
        if not doc_resp.data:
            raise ValueError("Document not found")

        stored_pdf_path = doc_resp.data[0].get('pdf_storage_path')
        pdf_storage = EncryptedSupabaseStorage('pdfs')
        pdf_bytes = None

        #  Try to download existing PDF; if it fails, compile from pages
        if stored_pdf_path:
            try:
                logger.info(f"Attempting to download existing PDF: {stored_pdf_path}")
                pdf_bytes = pdf_storage.download(
                    owner_id=user_id,
                    document_id=document_id,
                    storage_path=stored_pdf_path
                )
                logger.info("PDF downloaded successfully.")
            except Exception as e:
                logger.warning(f"Failed to download existing PDF: {e}. Will recompile from pages.")
                pdf_bytes = None

        #  If no PDF bytes, compile from pages
        if pdf_bytes is None:
            logger.info("Compiling PDF from pages...")
            # Fetch pages
            pages_resp = supabase.table('pages')\
                .select('id, image_storage_path, page_number')\
                .eq('document_id', document_id)\
                .order('page_number')\
                .execute()

            if not pages_resp.data:
                raise ValueError("No pages found for this document")

            image_storage = SupabaseStorage('scans')
            image_bytes_list = []
            for page in pages_resp.data:
                path = page['image_storage_path']
                if path.startswith('scans/'):
                    path = path[6:]
                img_bytes = image_storage.download(
                    owner_id=user_id,
                    document_id=document_id,
                    storage_path=path
                )
                image_bytes_list.append(img_bytes)

            pdf_bytes = merge_images_to_pdf(image_bytes_list)

            # Cache the compiled PDF (encrypted) for future use
            new_pdf_path = f"{user_id}/{document_id}/{uuid.uuid4().hex}.enc"
            pdf_storage.upload(
                owner_id=user_id,
                document_id=document_id,
                file_bytes=pdf_bytes,
                content_type='application/pdf'
            )
            # Update document with the new path
            supabase.table('documents').update({
                'pdf_storage_path': new_pdf_path,
                'page_count': len(image_bytes_list)
            }).eq('id', document_id).execute()
            logger.info(f"Compiled and uploaded new PDF: {new_pdf_path}")

        #  Convert the PDF to target format
        if target_format == 'docx':
            output_bytes = pdf_to_docx(pdf_bytes)
            content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            ext = 'docx'
        elif target_format == 'xlsx':
            output_bytes = pdf_to_xlsx(pdf_bytes)
            content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            ext = 'xlsx'
        elif target_format == 'csv':
            output_bytes = pdf_to_csv(pdf_bytes)
            content_type = 'text/csv'
            ext = 'csv'
        elif target_format == 'txt':
            output_bytes = pdf_to_txt(pdf_bytes)
            content_type = 'text/plain'
            ext = 'txt'
        elif target_format == 'jpg':
            output_bytes = pdf_to_jpg(pdf_bytes)
            content_type = 'image/jpeg'
            ext = 'jpg'
        elif target_format == 'png':
            output_bytes = pdf_to_png(pdf_bytes)
            content_type = 'image/png'
            ext = 'png'
        elif target_format == 'webp':
            output_bytes = pdf_to_webp(pdf_bytes)
            content_type = 'image/webp'
            ext = 'webp'
        elif target_format == 'pptx':
            output_bytes = pdf_to_pptx(pdf_bytes)
            content_type = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
            ext = 'pptx'
        elif target_format == 'long_image':
            output_bytes = pdf_to_long_image(pdf_bytes)
            content_type = 'image/png'
            ext = 'png'
        elif target_format == 'long_jpg':
            output_bytes = pdf_to_long_image_jpg(pdf_bytes)
            content_type = 'image/jpeg'
            ext = 'jpg'
        else:
            raise ValueError(f"Unsupported format: {target_format}")

        # Upload converted file
        converted_storage = EncryptedSupabaseStorage('converted')
        path = f"{user_id}/{document_id}/{uuid.uuid4().hex}.{ext}"
        storage_path = converted_storage.upload(
            owner_id=user_id,
            document_id=document_id,
            file_bytes=output_bytes,
            content_type=content_type
        )

        signed_url = supabase.storage.from_('converted').create_signed_url(storage_path, 60)

        job.result = signed_url
        job.status = 'done'
        job.error_message = None

    except Exception as e:
        job.status = 'failed'
        job.error_message = str(e)
        logger.exception(f"Conversion job {job_id} failed")

    finally:
        job.completed_at = timezone.now()
        job.save(update_fields=['status', 'result', 'error_message', 'completed_at'])