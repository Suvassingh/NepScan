from rest_framework import serializers
from .models import Organization, OrganizationMembership, Invitation

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['id', 'name', 'created_by', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

class OrganizationMembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationMembership
        fields = ['id', 'organization', 'user_id', 'role', 'joined_at']
        read_only_fields = ['id', 'joined_at']

class InvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invitation
        fields = ['id', 'organization', 'email', 'role', 'token', 'expires_at', 'accepted_at', 'created_at']
        read_only_fields = ['id', 'token', 'created_at']