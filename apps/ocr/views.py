from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from apps.authentication.permissions import IsOwnerOrShared
from common.response_wrappers import APIResponse
from apps.audit.services import log_document_access
from .models import ExtractedData, OCRJob, OCRResult
from .serializers import ExtractedDataSerializer, OCRRunSerializer, OCRStatusSerializer, OCRResultSerializer
from .tasks import run_ocr_job

class OCRViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated, IsOwnerOrShared]
    throttle_scope = 'ocr'

    @action(detail=False, methods=['post'])
    def run(self, request):
        serializer = OCRRunSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        doc_id = serializer.validated_data['document_id']

        # Avoid duplicate pending jobs
        existing_job = OCRJob.objects.filter(
            document_id=doc_id,
            job_type='ocr',
            status__in=['queued', 'running']
        ).first()
        if existing_job:
            return APIResponse({'job_id': str(existing_job.id)}, status=status.HTTP_202_ACCEPTED)

        job = OCRJob.objects.create(document_id=doc_id, job_type='ocr')
        run_ocr_job.delay(str(job.id), str(doc_id), str(request.user.id))
        return APIResponse({'job_id': str(job.id)}, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=['get'], url_path='status/(?P<document_id>[^/.]+)')
    def status(self, request, document_id):
        job = OCRJob.objects.filter(document_id=document_id, job_type='ocr').order_by('-created_at').first()
        if not job:
            return APIResponse({}, status=404, message='No OCR job found')
        serializer = OCRStatusSerializer(job)
        # Use keyword arguments
        log_document_access(
            event='viewed',
            user_id=request.user.id,
            document_id=document_id,
            ip=request.META.get('REMOTE_ADDR', 'unknown')
        )
        return APIResponse(serializer.data)

    @action(detail=False, methods=['get'], url_path='result/(?P<document_id>[^/.]+)')
    def result(self, request, document_id):
        result = OCRResult.objects.filter(document_id=document_id).order_by('-created_at').first()
        if not result:
            return APIResponse({}, status=404, message='No OCR result found')
        serializer = OCRResultSerializer(result)
        log_document_access(
            event='viewed',
            user_id=request.user.id,
            document_id=document_id,
            ip=request.META.get('REMOTE_ADDR', 'unknown')
        )
        return APIResponse(serializer.data)
    
    @action(detail=False, methods=['post'])
    def extract(self, request):
         
        serializer = OCRRunSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        doc_id = serializer.validated_data['document_id']

        # Check if extraction already exists
        existing = ExtractedData.objects.filter(document_id=doc_id).first()
        if existing:
            return APIResponse({'extracted_id': str(existing.id)}, status=200)

        # Trigger Celery task
        from .tasks import extract_structured_data_task
        task = extract_structured_data_task.delay(str(doc_id))
        return APIResponse({'task_id': task.id}, status=202)

    @action(detail=False, methods=['get'], url_path='extracted-data/(?P<document_id>[^/.]+)')
    def extracted_data(self, request, document_id):
        
        try:
            data = ExtractedData.objects.get(document_id=document_id)
            serializer = ExtractedDataSerializer(data)
            return APIResponse(serializer.data, status=200)
        except ExtractedData.DoesNotExist:
            return APIResponse({}, status=404, message='No extracted data found')