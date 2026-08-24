from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from common.response_wrappers import APIResponse
from apps.jobs.models import Job   
from .serializers import JobStatusSerializer    

class JobViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='(?P<job_id>[^/.]+)')
    def status(self, request, job_id):
         
        job = get_object_or_404(Job, id=job_id)
        
        serializer = JobStatusSerializer(job)
        return APIResponse(serializer.data)