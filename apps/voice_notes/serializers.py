from rest_framework import serializers
from .models import VoiceNote

class VoiceUploadSerializer(serializers.Serializer):
    document_id = serializers.UUIDField()
    audio_file = serializers.FileField()

class VoiceNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = VoiceNote
        fields = ['id', 'document_id', 'storage_path', 'transcript', 'created_at']