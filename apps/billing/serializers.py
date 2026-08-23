from rest_framework import serializers
from .models import DocumentShare, Subscription

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ['owner_id', 'plan', 'status', 'current_period_end', 'provider']
        read_only_fields = fields
        


class DocumentShareSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentShare
        fields = ['id', 'document_id', 'owner_id', 'shared_with_id', 'organization_id', 'permission', 'share_token', 'expires_at', 'created_at']
        read_only_fields = ['id', 'owner_id', 'created_at']