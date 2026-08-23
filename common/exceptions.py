 
import logging
import uuid
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger('scanline.errors')

 
_SIGNATURES = {
    b'\xff\xd8\xff': 'image/jpeg',
    b'\x89PNG\r\n\x1a\n': 'image/png',
    b'RIFF': 'image/webp',   
    b'%PDF-': 'application/pdf',
}

class UnsupportedFileType(Exception):
    pass

def sanitized_exception_handler(exc, context):
  
    response = exception_handler(exc, context)
    if response is not None:
        return response   

    
    error_id = uuid.uuid4().hex
    logger.exception('Unhandled exception [error_id=%s]', error_id, extra={'error_id': error_id})
    return Response(
        {'error': 'An unexpected error occurred.', 'error_id': error_id},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )

def validate_upload_magic_bytes(file_obj, declared_content_type: str) -> str:
    
    header = file_obj.read(16)
    file_obj.seek(0)

    if header.startswith(b'\xff\xd8\xff'):
        verified = 'image/jpeg'
    elif header.startswith(b'\x89PNG\r\n\x1a\n'):
        verified = 'image/png'
    elif header[0:4] == b'RIFF' and header[8:12] == b'WEBP':
        verified = 'image/webp'
    elif header.startswith(b'%PDF-'):
        verified = 'application/pdf'
    else:
        raise UnsupportedFileType('File signature does not match an allowed type')

     
    if declared_content_type and declared_content_type != verified:
        logger.warning(
            'Upload content‑type mismatch: declared=%s verified=%s',
            declared_content_type, verified
        )

    return verified