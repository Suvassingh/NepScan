import pytest
from rest_framework import status
from unittest.mock import patch
from apps.expense.models import ExpenseData
from .factories import ExpenseDataFactory

@pytest.mark.django_db
@patch('apps.expense.views.extract_expense.delay')
def test_expense_extract_endpoint(mock_delay, auth_client):
    mock_delay.return_value.id = 'mock-task'
    payload = {'document_id': '550e8400-e29b-41d4-a716-446655440000'}
    response = auth_client.post('/api/v1/expense/extract/', payload)
    assert response.status_code == status.HTTP_202_ACCEPTED

@pytest.mark.django_db
def test_expense_result_endpoint(auth_client):
    data = ExpenseDataFactory(document_id='550e8400-e29b-41d4-a716-446655440000')
    # Mock vendor decryption
    with patch('apps.expense.models.ExpenseData.vendor', new_callable=property) as mock_vendor:
        mock_vendor.return_value = 'Test Vendor'
        response = auth_client.get(f'/api/v1/expense/result/{data.document_id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['vendor'] == 'Test Vendor'