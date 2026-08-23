import pytest
from unittest.mock import patch
from rest_framework import status
from apps.ocr.models import OCRJob, OCRResult
from apps.ocr.tasks import run_ocr_job
from .factories import OCRJobFactory, OCRResultFactory

@pytest.mark.django_db
def test_ocr_run_endpoint(auth_client):
    payload = {'document_id': '550e8400-e29b-41d4-a716-446655440000'}
    response = auth_client.post('/api/v1/ocr/run/', payload)
    assert response.status_code == status.HTTP_202_ACCEPTED
    assert 'job_id' in response.data['data']
    job_id = response.data['data']['job_id']
    job = OCRJob.objects.get(id=job_id)
    assert job.document_id == payload['document_id']

@pytest.mark.django_db
def test_ocr_status_endpoint(auth_client):
    job = OCRJobFactory(document_id='550e8400-e29b-41d4-a716-446655440000')
    response = auth_client.get(f'/api/v1/ocr/status/{job.document_id}/')
    assert response.status_code == status.HTTP_200_OK
    assert response.data['data']['status'] == job.status

@pytest.mark.django_db
def test_ocr_result_endpoint(auth_client):
    result = OCRResultFactory(document_id='550e8400-e29b-41d4-a716-446655440000')
    # We need to mock the decryption to return a text
    with patch('apps.ocr.models.OCRResult.extracted_text', new_callable=property) as mock_text:
        mock_text.return_value = 'Test OCR text'
        response = auth_client.get(f'/api/v1/ocr/result/{result.document_id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['extracted_text'] == 'Test OCR text'

@pytest.mark.django_db
@patch('apps.ocr.tasks.perform_ocr')
def test_ocr_task(mock_perform_ocr):
    mock_perform_ocr.return_value = ('Sample text', 'ne+en', 0.98)
    job = OCRJobFactory()
    run_ocr_job(str(job.id), str(job.document_id), 'test-user')
    job.refresh_from_db()
    assert job.status == 'done'
    result = OCRResult.objects.get(document_id=job.document_id)
    assert result.extracted_text == 'Sample text'