import io
import logging
import uuid

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, render

from common.response_wrappers import APIResponse
from common.supabase_client import get_supabase_client
from common.encryption import EnvelopeEncryptor, EncryptionError
from common.storage.encrypted_storage import EncryptedSupabaseStorage

from apps.workspaces.models import OrganizationMembership

from .models import DocumentShare, Subscription
from .serializers import DocumentShareSerializer, SubscriptionSerializer
from .services.revenuecat_verifier import verify_webhook

logger = logging.getLogger(__name__)

 
@api_view(['GET'])
@permission_classes([AllowAny])
def share_preview(request, token):
    """Render a preview page for a shared document."""
    try:
        share = get_object_or_404(DocumentShare, share_token=token)

        if share.expires_at and share.expires_at < timezone.now():
            return render(request, 'share_preview.html', {
                'expired': True,
                'token': token,
            })

        supabase = get_supabase_client()
        doc_resp = supabase.table('documents').select('title, page_count, owner_id').eq('id', share.document_id).execute()

        if not doc_resp.data:
            return render(request, 'share_preview.html', {
                'error': 'Document not found',
                'error_detail': 'The document may have been deleted by the owner.',
                'token': token,
            })

        doc = doc_resp.data[0]

        owner_name = None
        if doc.get('owner_id'):
            profile_resp = supabase.table('profiles').select('full_name').eq('id', doc['owner_id']).execute()
            if profile_resp.data and profile_resp.data[0].get('full_name'):
                owner_name = profile_resp.data[0]['full_name']

        context = {
            'document_title': doc.get('title', 'Untitled Document'),
            'owner_name': owner_name or 'Unknown',
            'page_count': doc.get('page_count', 1),
            'expires_at': share.expires_at,
            'token': token,
            'expired': False,
        }
        return render(request, 'share_preview.html', context)

    except Http404:
        return render(request, 'share_preview.html', {
            'error': 'Invalid Share Link',
            'error_detail': 'The link you followed does not exist.',
        })
    except Exception as e:
        logger.exception(f"Share preview error for token {token}")
        return render(request, 'share_preview.html', {
            'error': 'Something went wrong',
            'error_detail': 'Please try again later.',
        })


@api_view(['GET'])
@permission_classes([AllowAny])
def share_download(request, token):
     
    try:
        share = get_object_or_404(DocumentShare, share_token=token)

        if share.expires_at and share.expires_at < timezone.now():
            return Response(
                {'error': 'This share link has expired.'},
                status=status.HTTP_410_GONE
            )

        supabase = get_supabase_client()
        doc_resp = supabase.table('documents').select('pdf_storage_path, title').eq('id', share.document_id).execute()

        if not doc_resp.data:
            return Response(
                {'error': 'Document not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        doc = doc_resp.data[0]
        pdf_path = doc.get('pdf_storage_path')

        if not pdf_path:
            return Response(
                {'error': 'No PDF available for this document.'},
                status=status.HTTP_404_NOT_FOUND
            )

        storage = EncryptedSupabaseStorage('pdfs')
        pdf_bytes = storage.download(
            owner_id=str(share.owner_id),
            document_id=str(share.document_id),
            storage_path=pdf_path
        )

        response = FileResponse(
            io.BytesIO(pdf_bytes),
            content_type='application/pdf',
            filename=f'document_{share.document_id}.pdf'
        )
        response['Content-Disposition'] = f'inline; filename="document_{share.document_id}.pdf"'
        return response

    except Http404:
        return Response(
            {'error': 'Invalid share link.'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.exception(f"Share download error for token {token}")
        return Response(
            {'error': 'An unexpected error occurred.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


 
class BillingViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def status(self, request):
        sub = Subscription.objects.get(owner_id=request.user.id)
        serializer = SubscriptionSerializer(sub)
        return APIResponse(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    @method_decorator(csrf_exempt)
    def webhook(self, request):
        if not verify_webhook(request):
            return APIResponse({}, status=401, message='Invalid signature')
        return APIResponse({}, status=200)


 
class SharingViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    queryset = DocumentShare.objects.none()

    @action(detail=False, methods=['post'])
    def share_document(self, request):
        doc_id = request.data.get('document_id')
        shared_with_id = request.data.get('shared_with_id')
        shared_with_email = request.data.get('shared_with_email')
        organization_id = request.data.get('organization_id')
        permission = request.data.get('permission', 'view')
        expires_at = request.data.get('expires_at')

        if not doc_id:
            return APIResponse({}, status=400, message='document_id required')

        supabase = get_supabase_client()
        doc_resp = supabase.table('documents').select('owner_id').eq('id', doc_id).execute()
        if not doc_resp.data or doc_resp.data[0]['owner_id'] != str(request.user.id):
            return APIResponse({}, status=403, message='You do not own this document')

        if shared_with_email:
            profiles_resp = supabase.table('profiles').select('id').eq('email', shared_with_email).execute()
            if not profiles_resp.data:
                return APIResponse({}, status=404, message='User with this email not found')
            shared_with_id = profiles_resp.data[0]['id']
        elif shared_with_id:
            try:
                uuid.UUID(shared_with_id)
            except ValueError:
                return APIResponse({}, status=400, message='Invalid UUID format for shared_with_id')
        else:
            if not organization_id:
                return APIResponse({}, status=400, message='Specify user (email/id) or organization')

        if organization_id:
            is_member = OrganizationMembership.objects.filter(
                organization_id=organization_id,
                user_id=request.user.id
            ).exists()
            if not is_member:
                return APIResponse({}, status=403, message='You are not a member of this organization')

        share = DocumentShare.objects.create(
            document_id=doc_id,
            owner_id=request.user.id,
            shared_with_id=shared_with_id,
            organization_id=organization_id,
            permission=permission,
            expires_at=expires_at
        )
        return APIResponse({'share_id': str(share.id)}, status=201)

    @action(detail=False, methods=['get'])
    def shared_with_me(self, request):
        individual_shares = DocumentShare.objects.filter(shared_with_id=request.user.id)
        memberships = OrganizationMembership.objects.filter(user_id=request.user.id)
        org_ids = memberships.values_list('organization_id', flat=True)
        org_shares = DocumentShare.objects.filter(organization_id__in=org_ids)
        all_shares = individual_shares | org_shares
        serializer = DocumentShareSerializer(all_shares, many=True)
        return APIResponse(serializer.data)

    @action(detail=False, methods=['post'])
    def generate_share_link(self, request):
        doc_id = request.data.get('document_id')
        if not doc_id:
            return APIResponse({}, status=400, message='document_id required')

        supabase = get_supabase_client()
        doc_resp = supabase.table('documents').select('owner_id').eq('id', doc_id).execute()
        if not doc_resp.data or doc_resp.data[0]['owner_id'] != str(request.user.id):
            return APIResponse({}, status=403, message='You do not own this document')

        token = uuid.uuid4().hex
         
        expires_at = timezone.now() + timezone.timedelta(days=7)
        share = DocumentShare.objects.create(
            document_id=doc_id,
            owner_id=request.user.id,
            share_token=token,
            permission='view',
            expires_at=expires_at
        )
        return APIResponse({'share_token': token}, status=201)