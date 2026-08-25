from rest_framework import serializers

class PDFCompileSerializer(serializers.Serializer):
    document_id = serializers.UUIDField()
    page_ids = serializers.ListField(child=serializers.UUIDField())

class PDFCompressSerializer(serializers.Serializer):
    document_id = serializers.UUIDField()
    quality = serializers.ChoiceField(choices=['low', 'medium', 'high'], default='medium')

class PDFProtectSerializer(serializers.Serializer):
    document_id = serializers.UUIDField()
    password = serializers.CharField(min_length=4, max_length=128)

class PDFWatermarkSerializer(serializers.Serializer):
    document_id = serializers.UUIDField()
    text = serializers.CharField(max_length=256)