import logging
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse

from apps.image_processing.services.timestamp_overlay import add_timestamp_to_image
from .services.edge_detector import detect_and_correct_perspective
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from .services.timestamp_overlay import add_timestamp_to_image
from apps.billing.models import StorageEncryptionMetadata
import io
logger = logging.getLogger(__name__)

class CorrectPerspectiveView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
         
        logger.info(f"Request method: {request.method}")
        logger.info(f"Content-Type: {request.content_type}")
        logger.info(f"FILES keys: {request.FILES.keys()}")
        logger.info(f"POST keys: {request.POST.keys()}")
        logger.info(f"Data: {request.data}")

         
        if 'image' not in request.FILES:
            logger.error("No 'image' field in request.FILES")
            logger.error(f"Available FILES: {request.FILES.keys()}")
            return Response(
                {'error': 'No image file provided. Available fields: ' + ', '.join(request.FILES.keys())},
                status=status.HTTP_400_BAD_REQUEST
            )

        file_obj = request.FILES['image']
        logger.info(f"File name: {file_obj.name}")
        logger.info(f"File size: {file_obj.size} bytes")
        logger.info(f"File content-type: {file_obj.content_type}")

        try:
            image_bytes = file_obj.read()
            corrected_bytes = detect_and_correct_perspective(image_bytes)

            if corrected_bytes is None:
                return Response(
                    {'error': 'No document edges found. Try taking a clearer photo.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return HttpResponse(
                corrected_bytes,
                content_type='image/jpeg',
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.exception("Perspective correction failed")
            return Response(
                {'error': f'Processing failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
class AddTimestampView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
         
        if 'image' not in request.FILES:
            return Response(
                {'error': 'No image provided'},
                status=400
            )
        
        file_obj = request.FILES['image']
        position = request.data.get('position', 'bottom-right')
        format = request.data.get('format', '%Y-%m-%d %H:%M:%S')
        
        try:
            image_bytes = file_obj.read()
            processed_bytes = add_timestamp_to_image(
                image_bytes,
                format=format,
                position=position
            )
            
            return HttpResponse(
                processed_bytes,
                content_type='image/jpeg',
                status=200
            )
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=500
            )