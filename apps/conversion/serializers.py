from rest_framework import serializers

class ConvertSerializer(serializers.Serializer):
    document_id = serializers.UUIDField()
    target_format = serializers.ChoiceField(choices=['pdf', 'jpg', 'png', 'webp', 'docx', 'xlsx', 'csv', 'txt','pptx','long_image', 'long_jpg'])
    
class ImportFileSerializer(serializers.Serializer):
    file = serializers.FileField()