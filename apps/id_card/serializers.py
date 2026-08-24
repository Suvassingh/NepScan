from rest_framework import serializers

class IDCombineSerializer(serializers.Serializer):
    document_id = serializers.UUIDField()
    front_page_id = serializers.UUIDField()
    back_page_id = serializers.UUIDField()