from rest_framework import serializers

class SummarizeSerializer(serializers.Serializer):
    document_id = serializers.UUIDField()

class AskSerializer(serializers.Serializer):
    document_id = serializers.UUIDField()
    question = serializers.CharField(max_length=500)