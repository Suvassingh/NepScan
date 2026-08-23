from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from apps.jobs.models import Job
from common.response_wrappers import APIResponse
from .serializers import ConvertSerializer
from .tasks import convert_document
from django.shortcuts import get_object_or_404
from common.supabase_client import get_supabase_client
from common.storage.encrypted_storage import EncryptedSupabaseStorage
from common.storage.supabase_storage import SupabaseStorage
from apps.pdf_tools.services.pdf_compiler import merge_images_to_pdf
from .serializers import ConvertSerializer
from .tasks import convert_document
import uuid
import logging

logger = logging.getLogger(__name__)

class ConversionViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def convert(self, request):
        serializer = ConvertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        doc_id = serializer.validated_data['document_id']
        target = serializer.validated_data['target_format']

        if target not in ['pdf', 'jpg', 'png', 'webp', 'docx', 'xlsx', 'csv', 'txt']:
            return APIResponse({}, status=400, message='Unsupported format')

        supabase = get_supabase_client()

        # Special case: PDF – return a real signed URL
        if target == 'pdf':
            # Get document info
            doc_resp = supabase.table('documents').select('pdf_storage_path').eq('id', doc_id).execute()
            if not doc_resp.data:
                return APIResponse({}, status=404, message='Document not found')

            existing_pdf_path = doc_resp.data[0].get('pdf_storage_path')
            pdf_storage = EncryptedSupabaseStorage('pdfs')

            # If PDF exists, generate signed URL and return
            if existing_pdf_path:
                try:
                    signed_url = supabase.storage.from_('pdfs').create_signed_url(existing_pdf_path, 60)
                    return APIResponse({'download_url': signed_url}, status=200)
                except Exception as e:
                    logger.warning(f"Could not generate signed URL for existing PDF {existing_pdf_path}: {e}")
                    # Fall through to recompile

            # No PDF or existing PDF is broken – compile from pages
            pages_resp = supabase.table('pages')\
                .select('id, image_storage_path, page_number')\
                .eq('document_id', doc_id)\
                .order('page_number')\
                .execute()

            if not pages_resp.data:
                return APIResponse({}, status=404, message='No pages found for this document')

            image_storage = SupabaseStorage('scans')
            image_bytes_list = []
            for page in pages_resp.data:
                path = page['image_storage_path']
                if path.startswith('scans/'):
                    path = path[6:]
                img_bytes = image_storage.download(
                    owner_id=str(request.user.id),
                    document_id=str(doc_id),
                    storage_path=path
                )
                image_bytes_list.append(img_bytes)

            pdf_bytes = merge_images_to_pdf(image_bytes_list)

            # Upload the compiled PDF – get the path from the storage operation
            new_pdf_path = f"{request.user.id}/{doc_id}/{uuid.uuid4().hex}.enc"
            uploaded_path = pdf_storage.upload(
                owner_id=str(request.user.id),
                document_id=str(doc_id),
                file_bytes=pdf_bytes,
                content_type='application/pdf'
            )
            # uploaded_path should be the same as new_pdf_path, but we use what was returned
            logger.info(f"Uploaded PDF to: {uploaded_path}")

            # Update document with the new PDF path
            supabase.table('documents').update({
                'pdf_storage_path': uploaded_path,
                'page_count': len(image_bytes_list)
            }).eq('id', doc_id).execute()

            # Generate signed URL for the newly uploaded PDF using the same path
            signed_url = supabase.storage.from_('pdfs').create_signed_url(uploaded_path, 60)
            return APIResponse({'download_url': signed_url}, status=200)

        # For other formats, trigger Celery task
        job = Job.objects.create(
            document_id=doc_id,
            job_type='conversion',
            status='queued'
        )
        convert_document.delay(str(job.id), str(doc_id), target, str(request.user.id))
        return APIResponse({'job_id': str(job.id)}, status=202)