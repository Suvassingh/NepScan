from celery import shared_task
from django.utils import timezone
from common.supabase_client import get_supabase_client
from common.storage.encrypted_storage import EncryptedSupabaseStorage
from .services.pdf_compiler import merge_images_to_pdf
from .services.pdf_compressor import compress_pdf as compress_func
from .services.pdf_protector import add_password
from .services.pdf_watermarker import add_watermark

@shared_task
def compile_pdf(document_id: str, page_ids: list, user_id: str):

    storage = EncryptedSupabaseStorage('scans')
    supabase = get_supabase_client()
    images = []
    for page_id in page_ids:
        resp = supabase.table('pages').select('image_storage_path').eq('id', page_id).execute()
        if resp.data:
            path = resp.data[0]['image_storage_path']
            img_bytes = storage.download(owner_id=user_id, document_id=document_id, storage_path=path)
            images.append(img_bytes)
    if not images:
        raise ValueError("No images found for the given page IDs")
    pdf_bytes = merge_images_to_pdf(images)
    pdf_storage = EncryptedSupabaseStorage('pdfs')
    pdf_path = pdf_storage.upload(
        owner_id=user_id,
        document_id=document_id,
        file_bytes=pdf_bytes,
        content_type='application/pdf'
    )
    supabase.table('documents').update({'pdf_storage_path': pdf_path}).eq('id', document_id).execute()
    return pdf_path

@shared_task
def compress_pdf(document_id: str, quality: str, user_id: str):

    supabase = get_supabase_client()
    # Get current PDF path
    resp = supabase.table('documents').select('pdf_storage_path').eq('id', document_id).execute()
    if not resp.data:
        raise ValueError("Document not found")
    pdf_path = resp.data[0].get('pdf_storage_path')
    if not pdf_path:
        raise ValueError("Document has no PDF to compress")
    # Download, compress, re-upload
    storage = EncryptedSupabaseStorage('pdfs')
    pdf_bytes = storage.download(owner_id=user_id, document_id=document_id, storage_path=pdf_path)
    compressed = compress_func(pdf_bytes, quality)
    new_path = storage.upload(
        owner_id=user_id,
        document_id=document_id,
        file_bytes=compressed,
        content_type='application/pdf'
    )
    supabase.table('documents').update({'pdf_storage_path': new_path}).eq('id', document_id).execute()
    return new_path

@shared_task
def protect_pdf(document_id: str, password: str, user_id: str):

    supabase = get_supabase_client()
    resp = supabase.table('documents').select('pdf_storage_path').eq('id', document_id).execute()
    if not resp.data:
        raise ValueError("Document not found")
    pdf_path = resp.data[0].get('pdf_storage_path')
    if not pdf_path:
        raise ValueError("Document has no PDF to protect")
    storage = EncryptedSupabaseStorage('pdfs')
    pdf_bytes = storage.download(owner_id=user_id, document_id=document_id, storage_path=pdf_path)
    protected = add_password(pdf_bytes, password)
    new_path = storage.upload(
        owner_id=user_id,
        document_id=document_id,
        file_bytes=protected,
        content_type='application/pdf'
    )
    supabase.table('documents').update({'pdf_storage_path': new_path, 'is_password_protected': True}).eq('id', document_id).execute()
    return new_path

@shared_task
def watermark_pdf(document_id: str, text: str, user_id: str):

    supabase = get_supabase_client()
    resp = supabase.table('documents').select('pdf_storage_path').eq('id', document_id).execute()
    if not resp.data:
        raise ValueError("Document not found")
    pdf_path = resp.data[0].get('pdf_storage_path')
    if not pdf_path:
        raise ValueError("Document has no PDF to watermark")
    storage = EncryptedSupabaseStorage('pdfs')
    pdf_bytes = storage.download(owner_id=user_id, document_id=document_id, storage_path=pdf_path)
    watermarked = add_watermark(pdf_bytes, text)
    new_path = storage.upload(
        owner_id=user_id,
        document_id=document_id,
        file_bytes=watermarked,
        content_type='application/pdf'
    )
    supabase.table('documents').update({'pdf_storage_path': new_path}).eq('id', document_id).execute()
    return new_path