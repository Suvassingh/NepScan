from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
import uuid
import hashlib
from .models import Organization, OrganizationMembership, Invitation
from .serializers import OrganizationSerializer, OrganizationMembershipSerializer, InvitationSerializer
from common.response_wrappers import APIResponse
from apps.audit.services import log_admin_event

class IsOrganizationMember(permissions.BasePermission):
    def has_permission(self, request, view):
        org_id = view.kwargs.get('org_id')
        if not org_id:
            return False
        return OrganizationMembership.objects.filter(
            organization_id=org_id,
            user_id=request.user.id
        ).exists()

class OrganizationViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        memberships = OrganizationMembership.objects.filter(user_id=self.request.user.id)
        org_ids = memberships.values_list('organization_id', flat=True)
        return Organization.objects.filter(id__in=org_ids)

    def perform_create(self, serializer):
        with transaction.atomic():
            org = serializer.save(created_by=self.request.user.id)
            OrganizationMembership.objects.create(
                organization=org,
                user_id=self.request.user.id,
                role='owner'
            )

    @action(detail=True, methods=['post'])
    def invite(self, request, pk=None):
        org = self.get_object()
        email = request.data.get('email')
        role = request.data.get('role', 'member')
        if not email:
            return APIResponse({}, status=400, message='Email required')

        # Generate a unique token
        token = hashlib.sha256(f"{org.id}{email}{uuid.uuid4()}".encode()).hexdigest()
        expires_at = timezone.now() + timezone.timedelta(days=7)

        invitation = Invitation.objects.create(
            organization=org,
            email=email,
            role=role,
            invited_by=request.user.id,
            token=token,
            expires_at=expires_at
        )

        
        log_admin_event(event='invite_sent', admin_id=request.user.id, ip=request.META.get('REMOTE_ADDR'))

        return APIResponse({'token': token, 'expires_at': expires_at}, status=201)

    @action(detail=False, methods=['post'], url_path='accept-invite')
    def accept_invite(self, request):
        token = request.data.get('token')
        if not token:
            return APIResponse({}, status=400, message='Token required')

        try:
            invitation = Invitation.objects.get(token=token, accepted_at__isnull=True)
        except Invitation.DoesNotExist:
            return APIResponse({}, status=404, message='Invalid or expired invitation')

        if invitation.expires_at < timezone.now():
            return APIResponse({}, status=400, message='Invitation expired')

        
        with transaction.atomic():
            OrganizationMembership.objects.create(
                organization=invitation.organization,
                user_id=request.user.id,
                role=invitation.role,
                invited_by=invitation.invited_by
            )
            invitation.accepted_at = timezone.now()
            invitation.save()

        return APIResponse({'message': 'Invitation accepted'}, status=200)