from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from common.response_wrappers import APIResponse
from .serializers import IDCombineSerializer
from .tasks import combine_id_cards

class IDCardViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def combine(self, request):
        serializer = IDCombineSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        doc_id = serializer.validated_data['document_id']
        front = serializer.validated_data['front_page_id']
        back = serializer.validated_data['back_page_id']
        job = combine_id_cards.delay(str(doc_id), str(front), str(back), str(request.user.id))
        return APIResponse({'job_id': job.id}, status=status.HTTP_202_ACCEPTED)