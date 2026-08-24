from celery import shared_task
from .services.id_combiner import combine_id_images

@shared_task
def combine_id_cards(document_id: str, front_page_id: str, back_page_id: str, user_id: str):
 
    from common.supabase_client import get_supabase_client
    from common.storage.encrypted_storage import EncryptedSupabaseStorage

    supabase = get_supabase_client()
    storage = EncryptedSupabaseStorage('scans')

     
    front_resp = supabase.table('pages').select('image_storage_path').eq('id', front_page_id).execute()
    back_resp = supabase.table('pages').select('image_storage_path').eq('id', back_page_id).execute()
    if not front_resp.data or not back_resp.data:
        raise ValueError("One or both pages not found")

    front_path = front_resp.data[0]['image_storage_path']
    back_path = back_resp.data[0]['image_storage_path']

    front_bytes = storage.download(owner_id=user_id, document_id=document_id, storage_path=front_path)
    back_bytes = storage.download(owner_id=user_id, document_id=document_id, storage_path=back_path)

    pdf_bytes = combine_id_images(front_bytes, back_bytes)

    pdf_storage = EncryptedSupabaseStorage('pdfs')
    pdf_path = pdf_storage.upload(
        owner_id=user_id,
        document_id=document_id,
        file_bytes=pdf_bytes,
        content_type='application/pdf'
    )
    supabase.table('documents').update({'pdf_storage_path': pdf_path}).eq('id', document_id).execute()
    return pdf_path