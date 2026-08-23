import pytest
from unittest.mock import patch
from rest_framework import status
from apps.pdf_tools.tasks import compile_pdf

@pytest.mark.django_db
@patch('apps.pdf_tools.views.compile_pdf.delay')
def test_pdf_compile_endpoint(mock_delay, auth_client):
    mock_delay.return_value.id = 'mock-task-id'
    payload = {'document_id': '550e8400-e29b-41d4-a716-446655440000', 'page_ids': ['page1', 'page2']}
    response = auth_client.post('/api/v1/pdf/compile/', payload)
    assert response.status_code == status.HTTP_202_ACCEPTED
    assert 'job_id' in response.data['data']

@pytest.mark.django_db
def test_pdf_compress_endpoint(auth_client):
    payload = {'document_id': '550e8400-e29b-41d4-a716-446655440000', 'quality': 'medium'}
    response = auth_client.post('/api/v1/pdf/compress/', payload)
    assert response.status_code == status.HTTP_202_ACCEPTED

@pytest.mark.django_db
def test_pdf_protect_endpoint(auth_client):
    payload = {'document_id': '550e8400-e29b-41d4-a716-446655440000', 'password': 'secure123'}
    response = auth_client.post('/api/v1/pdf/protect/', payload)
    assert response.status_code == status.HTTP_202_ACCEPTED

@pytest.mark.django_db
def test_pdf_watermark_endpoint(auth_client):
    payload = {'document_id': '550e8400-e29b-41d4-a716-446655440000', 'text': 'CONFIDENTIAL'}
    response = auth_client.post('/api/v1/pdf/watermark/', payload)
    assert response.status_code == status.HTTP_202_ACCEPTED