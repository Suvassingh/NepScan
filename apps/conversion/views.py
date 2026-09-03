from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from apps.jobs.models import Job
from common.response_wrappers import APIResponse
from .serializers import ConvertSerializer
from .tasks import convert_document
from django.shortcuts import get_object_or_404
from common.supabase_client import get_supabase_client
from common.storage.encrypted_storage import EncryptedSupabaseStorage
from common.storage.supabase_storage import SupabaseStorage
from apps.pdf_tools.services.pdf_compiler import merge_images_to_pdf
from .serializers import ConvertSerializer
from .tasks import convert_document
import uuid
import logging
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import uuid
import os
from PIL import Image
import io
from pypdf import PdfReader
import magic
from datetime import datetime

class ConversionViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @action(detail=False, methods=['post'])
    def import_file(self, request):

        if 'file' not in request.FILES:
            return APIResponse({}, status=400, message='No file provided')

        uploaded_file = request.FILES['file']
        file_name = uploaded_file.name
        file_size = uploaded_file.size

        # Validate file type
        allowed_types = [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # docx
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',       # xlsx
            'image/jpeg',
            'image/png',
            'image/webp',
            'image/gif',
            'application/msword',  # doc
            'application/vnd.ms-excel',  # xls
        ]

        # Use python-magic to detect MIME type
        try:
            file_bytes = uploaded_file.read()
            mime_type = magic.from_buffer(file_bytes, mime=True)
        except:
            # Fallback to content_type
            mime_type = uploaded_file.content_type

        if mime_type not in allowed_types:
            return APIResponse(
                {}, 
                status=400, 
                message=f'Unsupported file type: {mime_type}'
            )

        # Create document record
        supabase = get_supabase_client()
        doc_id = str(uuid.uuid4())
        user_id = str(request.user.id)
        now = datetime.now().isoformat()

        # Determine doc_type from file extension
        ext = os.path.splitext(file_name)[1].lower()
        doc_type_map = {
            '.pdf': 'pdf',
            '.docx': 'document',
            '.doc': 'document',
            '.xlsx': 'spreadsheet',
            '.xls': 'spreadsheet',
            '.jpg': 'image',
            '.jpeg': 'image',
            '.png': 'image',
            '.webp': 'image',
            '.gif': 'image',
        }
        doc_type = doc_type_map.get(ext, 'document')

        # Upload file to Supabase Storage (scans bucket)
        storage = EncryptedSupabaseStorage('scans')
        storage_path = f"{user_id}/{doc_id}/{uuid.uuid4().hex}_{file_name}"

        # For images, we can process and compress
        if mime_type.startswith('image/'):
            # Open image, resize if too large, convert to JPEG for consistency
            try:
                img = Image.open(io.BytesIO(file_bytes))
                # Resize if width > 2000px
                if img.width > 2000:
                    ratio = 2000 / img.width
                    new_size = (2000, int(img.height * ratio))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                output = io.BytesIO()
                img.save(output, format='JPEG', quality=85)
                file_bytes = output.getvalue()
                # Update file_name to .jpg
                file_name = os.path.splitext(file_name)[0] + '.jpg'
            except Exception as e:
                # If image processing fails, use original
                pass

            # Upload processed image
            uploaded_path = storage.upload(
                owner_id=user_id,
                document_id=doc_id,
                file_bytes=file_bytes,
                content_type='image/jpeg'
            )

            # Create document with 1 page
            doc_data = {
                'id': doc_id,
                'owner_id': user_id,
                'title': os.path.splitext(file_name)[0],
                'doc_type': doc_type,
                'page_count': 1,
                'file_size_bytes': len(file_bytes),
                'original_storage_path': uploaded_path,
                'created_at': now,
                'updated_at': now,
            }
            supabase.table('documents').insert(doc_data).execute()

            # Create page record
            page_data = {
                'id': str(uuid.uuid4()),
                'document_id': doc_id,
                'page_number': 1,
                'image_storage_path': uploaded_path,
            }
            supabase.table('pages').insert(page_data).execute()

            return APIResponse({
                'document_id': doc_id,
                'page_count': 1,
            }, status=201)

        # For PDFs, extract pages as images and create pages
        elif mime_type == 'application/pdf':
            try:
                from pypdf import PdfReader
                import io
                from pdf2image import convert_from_bytes
                
                # Upload PDF to storage
                uploaded_path = storage.upload(
                    owner_id=user_id,
                    document_id=doc_id,
                    file_bytes=file_bytes,
                    content_type='application/pdf'
                )

                # Convert PDF pages to images (for preview)
                page_count = 0
                try:
                    # Try to convert PDF to images
                    images = convert_from_bytes(file_bytes, dpi=150)
                    page_count = len(images)
                    
                    for i, img in enumerate(images):
                        img_byte_arr = io.BytesIO()
                        img.save(img_byte_arr, format='JPEG', quality=80)
                        img_bytes = img_byte_arr.getvalue()
                        
                        page_path = f"{user_id}/{doc_id}/{uuid.uuid4().hex}_page_{i+1}.jpg"
                        page_upload_path = storage.upload(
                            owner_id=user_id,
                            document_id=doc_id,
                            file_bytes=img_bytes,
                            content_type='image/jpeg'
                        )
                        
                        page_data = {
                            'id': str(uuid.uuid4()),
                            'document_id': doc_id,
                            'page_number': i + 1,
                            'image_storage_path': page_upload_path,
                        }
                        supabase.table('pages').insert(page_data).execute()
                except:
                    # If pdf2image fails, just count pages
                    reader = PdfReader(io.BytesIO(file_bytes))
                    page_count = len(reader.pages)
                    # Create placeholder pages (no images)
                    for i in range(page_count):
                        page_data = {
                            'id': str(uuid.uuid4()),
                            'document_id': doc_id,
                            'page_number': i + 1,
                            'image_storage_path': '',   
                        }
                        supabase.table('pages').insert(page_data).execute()

                # Create document
                doc_data = {
                    'id': doc_id,
                    'owner_id': user_id,
                    'title': os.path.splitext(file_name)[0],
                    'doc_type': doc_type,
                    'page_count': page_count,
                    'file_size_bytes': len(file_bytes),
                    'pdf_storage_path': uploaded_path,
                    'created_at': now,
                    'updated_at': now,
                }
                supabase.table('documents').insert(doc_data).execute()

                return APIResponse({
                    'document_id': doc_id,
                    'page_count': page_count,
                }, status=201)

            except Exception as e:
                return APIResponse({}, status=500, message=f'PDF processing failed: {str(e)}')

         
        else:
            
            uploaded_path = storage.upload(
                owner_id=user_id,
                document_id=doc_id,
                file_bytes=file_bytes,
                content_type=mime_type
            )

            doc_data = {
                'id': doc_id,
                'owner_id': user_id,
                'title': os.path.splitext(file_name)[0],
                'doc_type': doc_type,
                'page_count': 1,
                'file_size_bytes': len(file_bytes),
                'original_storage_path': uploaded_path,
                'created_at': now,
                'updated_at': now,
            }
            supabase.table('documents').insert(doc_data).execute()

            # Create a placeholder page
            page_data = {
                'id': str(uuid.uuid4()),
                'document_id': doc_id,
                'page_number': 1,
                'image_storage_path': uploaded_path,
            }
            supabase.table('pages').insert(page_data).execute()

            return APIResponse({
                'document_id': doc_id,
                'page_count': 1,
            }, status=201)
