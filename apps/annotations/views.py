from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from common.response_wrappers import APIResponse
from common.supabase_client import get_supabase_client
from .models import Annotation
from .serializers import AnnotationSerializer
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser  

class IsDocumentOwner(permissions.BasePermission):
     
    def has_permission(self, request, view):
         
        return True

    def has_object_permission(self, request, view, obj):
       
        supabase = get_supabase_client()
        doc_resp = supabase.table('documents').select('owner_id').eq('id', obj.document_id).execute()
        if doc_resp.data and doc_resp.data[0]['owner_id'] == str(request.user.id):
            return True
        return False

class AnnotationViewSet(viewsets.ModelViewSet):
    serializer_class = AnnotationSerializer
    permission_classes = [permissions.IsAuthenticated, IsDocumentOwner]
    parser_classes = [JSONParser, MultiPartParser, FormParser]  


    def get_queryset(self):
         
        return Annotation.objects.filter(user_id=self.request.user.id)

    def perform_create(self, serializer):
        serializer.save(user_id=self.request.user.id)

    def create(self, request, *args, **kwargs):
         
        doc_id = request.data.get('document_id')
        if not doc_id:
            return APIResponse({}, status=400, message='document_id required')
        supabase = get_supabase_client()
        doc_resp = supabase.table('documents').select('owner_id').eq('id', doc_id).execute()
        if not doc_resp.data or doc_resp.data[0]['owner_id'] != str(request.user.id):
            return APIResponse({}, status=403, message='You do not own this document')
        return super().create(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def list_for_document(self, request):
         
        doc_id = request.query_params.get('document_id')
        page_num = request.query_params.get('page_number', 1)
        if not doc_id:
            return APIResponse({}, status=400, message='document_id required')
         
        supabase = get_supabase_client()
        doc_resp = supabase.table('documents').select('owner_id').eq('id', doc_id).execute()
        if not doc_resp.data:
            return APIResponse({}, status=404, message='Document not found')
        if doc_resp.data[0]['owner_id'] != str(request.user.id):
             
            return APIResponse({}, status=403, message='Access denied')
        annotations = Annotation.objects.filter(document_id=doc_id, page_number=page_num)
        serializer = self.get_serializer(annotations, many=True)
        return APIResponse(serializer.data)