from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from common.response_wrappers import APIResponse
from .serializers import VoiceUploadSerializer, VoiceNoteSerializer
from .models import VoiceNote
from .tasks import transcribe_audio

class VoiceNoteViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def upload(self, request):
        serializer = VoiceUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        doc_id = serializer.validated_data['document_id']
        audio = serializer.validated_data['audio_file']

        voice = VoiceNote.objects.create(
            document_id=doc_id,
            owner_id=request.user.id,
            storage_path='some_path' 
            
        )
        transcribe_audio.delay(str(voice.id))
        return APIResponse({'voice_note_id': str(voice.id)}, status=201)

    @action(detail=False, methods=['get'], url_path='(?P<document_id>[^/.]+)')
    def list_for_document(self, request, document_id):
        notes = VoiceNote.objects.filter(document_id=document_id)
        serializer = VoiceNoteSerializer(notes, many=True)
        return APIResponse(serializer.data)