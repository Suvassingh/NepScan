from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from common.response_wrappers import APIResponse
from .serializers import ExpenseExtractSerializer, ExpenseDataSerializer
from .tasks import extract_expense
from .models import ExpenseData

class ExpenseViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def extract(self, request):
        serializer = ExpenseExtractSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        doc_id = serializer.validated_data['document_id']
        job = extract_expense.delay(str(doc_id), str(request.user.id))
        return APIResponse({'job_id': job.id}, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=['get'], url_path='result/(?P<document_id>[^/.]+)')
    def result(self, request, document_id):
        data = ExpenseData.objects.get(document_id=document_id)
        serializer = ExpenseDataSerializer(data)
        return APIResponse(serializer.data)

    @action(detail=False, methods=['post'])
    def export_ledger(self, request):
         
        return APIResponse({'message': 'Export started'}, status=202)