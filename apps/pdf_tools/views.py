from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from common.response_wrappers import APIResponse
from .serializers import (
    PDFCompileSerializer, PDFCompressSerializer,
    PDFProtectSerializer, PDFWatermarkSerializer
)
from .tasks import compile_pdf, compress_pdf, protect_pdf, watermark_pdf
from rest_framework.decorators import action
from common.supabase_client import get_supabase_client

@action(detail=False, methods=['post'])
def get_pdf_url(self, request):
    doc_id = request.data.get('document_id')
    supabase = get_supabase_client()
    doc_resp = supabase.table('documents').select('pdf_storage_path').eq('id', doc_id).execute()
    if not doc_resp.data or not doc_resp.data[0].get('pdf_storage_path'):
        return APIResponse({}, status=404, message='PDF not found')
    storage_path = doc_resp.data[0]['pdf_storage_path']
    # Generate signed URL (valid for 60 seconds)
    signed_url = supabase.storage.from_('pdfs').createSignedUrl(storage_path, 60)
    return APIResponse({'download_url': signed_url}, status=200)
class PDFToolsViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    throttle_scope = 'pdf_protect'

    @action(detail=False, methods=['post'])
    def compile(self, request):
        serializer = PDFCompileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        doc_id = serializer.validated_data['document_id']
        page_ids = serializer.validated_data['page_ids']
        job = compile_pdf.delay(str(doc_id), [str(p) for p in page_ids], str(request.user.id))
        return APIResponse({'job_id': job.id}, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=['post'])
    def compress(self, request):
        serializer = PDFCompressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        doc_id = serializer.validated_data['document_id']
        quality = serializer.validated_data['quality']
        job = compress_pdf.delay(str(doc_id), quality, str(request.user.id))
        return APIResponse({'job_id': job.id}, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=['post'])
    def protect(self, request):
        serializer = PDFProtectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        doc_id = serializer.validated_data['document_id']
        password = serializer.validated_data['password']
        job = protect_pdf.delay(str(doc_id), password, str(request.user.id))
        return APIResponse({'job_id': job.id}, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=['post'])
    def watermark(self, request):
        serializer = PDFWatermarkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        doc_id = serializer.validated_data['document_id']
        text = serializer.validated_data['text']
        job = watermark_pdf.delay(str(doc_id), text, str(request.user.id))
        return APIResponse({'job_id': job.id}, status=status.HTTP_202_ACCEPTED)