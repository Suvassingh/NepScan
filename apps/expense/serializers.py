from rest_framework import serializers
from .models import ExpenseData

class ExpenseExtractSerializer(serializers.Serializer):
    document_id = serializers.UUIDField()

class ExpenseDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseData
        fields = ['document_id', 'vendor', 'expense_date', 'category', 'amount', 'currency']
        read_only_fields = fields