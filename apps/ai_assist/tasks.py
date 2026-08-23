from celery import shared_task
from apps.ocr.models import OCRResult
from .services.summarizer import generate_summary
from .services.qa_engine import answer_question

@shared_task
def summarize_document(document_id: str, user_id: str):
    result = OCRResult.objects.get(document_id=document_id)
    text = result.extracted_text
    summary = generate_summary(text)
    result.ai_summary = summary
    result.save(update_fields=['ai_summary'])
    return summary

@shared_task
def ask_document(document_id: str, question: str, user_id: str):
    result = OCRResult.objects.get(document_id=document_id)
    answer = answer_question(result.extracted_text, question)
    return answer