from rest_framework import serializers
from .models import Job

class JobStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ['id', 'job_type', 'status', 'result', 'error_message', 'created_at', 'completed_at']