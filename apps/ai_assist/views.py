from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from common.response_wrappers import APIResponse
from .serializers import SummarizeSerializer, AskSerializer
from .tasks import summarize_document, ask_document

class AIAssistViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    throttle_scope = 'default'

    @action(detail=False, methods=['post'])
    def summarize(self, request):
        serializer = SummarizeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        doc_id = serializer.validated_data['document_id']
        job = summarize_document.delay(str(doc_id), str(request.user.id))
        return APIResponse({'job_id': job.id}, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=['post'])
    def ask(self, request):
        serializer = AskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        doc_id = serializer.validated_data['document_id']
        question = serializer.validated_data['question']
        job = ask_document.delay(str(doc_id), question, str(request.user.id))
        return APIResponse({'job_id': job.id}, status=status.HTTP_202_ACCEPTED)