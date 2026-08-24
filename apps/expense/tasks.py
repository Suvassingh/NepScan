from celery import shared_task
from .models import ExpenseData
from .services.receipt_parser import parse_receipt

@shared_task
def extract_expense(document_id: str, user_id: str):
     
    vendor, date, category, amount = parse_receipt(document_id)
    data, _ = ExpenseData.objects.get_or_create(document_id=document_id)
    data.vendor = vendor
    data.expense_date = date
    data.category = category
    data.amount = amount
    data.save()
    return data.id