from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response

from apps.jobs.models import Job
from common.response_wrappers import APIResponse
from common.supabase_client import get_supabase_client
from common.storage.encrypted_storage import EncryptedSupabaseStorage
from common.storage.supabase_storage import SupabaseStorage
from apps.pdf_tools.services.pdf_compiler import merge_images_to_pdf
from .serializers import ConvertSerializer
from .tasks import convert_document

import uuid
import logging
import io
import os
import magic
from datetime import datetime
from PIL import Image
from pypdf import PdfReader

logger = logging.getLogger(__name__)


class ConversionViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    @action(
        detail=False,
        methods=['post'],
        parser_classes=[MultiPartParser, FormParser]
    )
    def import_file(self, request):
        if 'file' not in request.FILES:
            return APIResponse({}, status=400, message='No file provided')

        uploaded_file = request.FILES['file']
        file_name = uploaded_file.name

        allowed_types = [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'image/jpeg',
            'image/png',
            'image/webp',
            'image/gif',
            'application/msword',
            'application/vnd.ms-excel',
        ]

        try:
            file_bytes = uploaded_file.read()
            mime_type = magic.from_buffer(file_bytes, mime=True)
        except:
            mime_type = uploaded_file.content_type

        if mime_type not in allowed_types:
            return APIResponse(
                {},
                status=400,
                message=f'Unsupported file type: {mime_type}'
            )

        supabase = get_supabase_client()
        doc_id = str(uuid.uuid4())
        user_id = str(request.user.id)
        now = datetime.now().isoformat()

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

        storage = EncryptedSupabaseStorage('scans')
        storage_path = f"{user_id}/{doc_id}/{uuid.uuid4().hex}_{file_name}"

        if mime_type.startswith('image/'):
            try:
                img = Image.open(io.BytesIO(file_bytes))
                if img.width > 2000:
                    ratio = 2000 / img.width
                    new_size = (2000, int(img.height * ratio))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                output = io.BytesIO()
                img.save(output, format='JPEG', quality=85)
                file_bytes = output.getvalue()
                file_name = os.path.splitext(file_name)[0] + '.jpg'
            except Exception as e:
                pass

            uploaded_path = storage.upload(
                owner_id=user_id,
                document_id=doc_id,
                file_bytes=file_bytes,
                content_type='image/jpeg'
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

        elif mime_type == 'application/pdf':
            try:
                from pdf2image import convert_from_bytes

                uploaded_path = storage.upload(
                    owner_id=user_id,
                    document_id=doc_id,
                    file_bytes=file_bytes,
                    content_type='application/pdf'
                )

                page_count = 0
                try:
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
                    reader = PdfReader(io.BytesIO(file_bytes))
                    page_count = len(reader.pages)
                    for i in range(page_count):
                        page_data = {
                            'id': str(uuid.uuid4()),
                            'document_id': doc_id,
                            'page_number': i + 1,
                            'image_storage_path': '',
                        }
                        supabase.table('pages').insert(page_data).execute()

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

    @action(detail=False, methods=['post'])
    def convert(self, request):
        serializer = ConvertSerializer(data=request.data)
        if not serializer.is_valid():
            return APIResponse(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
                message='Validation failed'
            )

        doc_id = serializer.validated_data['document_id']
        target = serializer.validated_data['target_format']

        valid_formats = ['pdf', 'jpg', 'png', 'webp', 'docx', 'xlsx', 'csv', 'txt']
        if target not in valid_formats:
            return APIResponse(
                {},
                status=400,
                message=f'Unsupported format. Choose from: {", ".join(valid_formats)}'
            )

        supabase = get_supabase_client()
        user_id = str(request.user.id)

        if target == 'pdf':
            doc_resp = supabase.table('documents')\
                .select('pdf_storage_path')\
                .eq('id', doc_id)\
                .execute()

            if not doc_resp.data:
                return APIResponse(
                    {},
                    status=404,
                    message='Document not found'
                )

            existing_pdf_path = doc_resp.data[0].get('pdf_storage_path')
            pdf_storage = EncryptedSupabaseStorage('pdfs')

            if existing_pdf_path:
                try:
                    signed_url = supabase.storage.from_('pdfs').create_signed_url(
                        existing_pdf_path, 60
                    )
                    return APIResponse(
                        {'download_url': signed_url},
                        status=200
                    )
                except Exception as e:
                    logger.warning(
                        f"Could not generate signed URL for existing PDF {existing_pdf_path}: {e}"
                    )

            pages_resp = supabase.table('pages')\
                .select('id, image_storage_path, page_number')\
                .eq('document_id', doc_id)\
                .order('page_number')\
                .execute()

            if not pages_resp.data:
                return APIResponse(
                    {},
                    status=404,
                    message='No pages found for this document'
                )

            image_storage = SupabaseStorage('scans')
            image_bytes_list = []

            for page in pages_resp.data:
                path = page['image_storage_path']
                if path.startswith('scans/'):
                    path = path[6:]

                img_bytes = image_storage.download(
                    owner_id=user_id,
                    document_id=str(doc_id),
                    storage_path=path
                )
                image_bytes_list.append(img_bytes)

            pdf_bytes = merge_images_to_pdf(image_bytes_list)

            new_pdf_path = f"{user_id}/{doc_id}/{uuid.uuid4().hex}.enc"
            uploaded_path = pdf_storage.upload(
                owner_id=user_id,
                document_id=str(doc_id),
                file_bytes=pdf_bytes,
                content_type='application/pdf'
            )

            logger.info(f"Uploaded PDF to: {uploaded_path}")

            supabase.table('documents').update({
                'pdf_storage_path': uploaded_path,
                'page_count': len(image_bytes_list)
            }).eq('id', doc_id).execute()

            signed_url = supabase.storage.from_('pdfs').create_signed_url(
                uploaded_path, 60
            )

            return APIResponse(
                {'download_url': signed_url},
                status=200
            )

        job = Job.objects.create(
            document_id=doc_id,
            job_type='conversion',
            status='queued'
        )

        convert_document.delay(
            str(job.id),
            str(doc_id),
            target,
            str(request.user.id)
        )

        return APIResponse(
            {'job_id': str(job.id)},
            status=202,
            message='Conversion started'
        )