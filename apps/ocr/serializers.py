from rest_framework import serializers
from .models import OCRJob, OCRResult
from .models import ExtractedData

class OCRRunSerializer(serializers.Serializer):
    document_id = serializers.UUIDField()

class OCRStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = OCRJob
        fields = ['id', 'status', 'error_message', 'completed_at']

class OCRResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = OCRResult
        fields = ['document_id', 'extracted_text', 'detected_language', 'confidence', 'ai_summary']
        read_only_fields = fields
        

class ExtractedDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtractedData
        fields = ['id', 'document_id', 'doc_type', 'data', 'confidence', 'created_at', 'updated_at']