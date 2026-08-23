import factory
import uuid
from datetime import datetime, timedelta
from apps.ocr.models import OCRJob, OCRResult
from apps.expense.models import ExpenseData
from apps.billing.models import Subscription

class OCRJobFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OCRJob
    id = factory.LazyFunction(uuid.uuid4)
    document_id = factory.LazyFunction(uuid.uuid4)
    job_type = 'ocr'
    status = 'queued'
    created_at = factory.LazyFunction(datetime.now)

class OCRResultFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OCRResult
    id = factory.LazyFunction(uuid.uuid4)
    document_id = factory.LazyFunction(uuid.uuid4)
    extracted_text_encrypted = 'encrypted-placeholder'
    detected_language = 'ne+en'
    confidence = 0.95

class ExpenseDataFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ExpenseData
    id = factory.LazyFunction(uuid.uuid4)
    document_id = factory.LazyFunction(uuid.uuid4)
    vendor_encrypted = 'encrypted-vendor'
    expense_date = factory.LazyFunction(datetime.now)
    category = 'Groceries'
    amount = 100.50
    currency = 'NPR'

class SubscriptionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Subscription
    id = factory.LazyFunction(uuid.uuid4)
    owner_id = factory.LazyFunction(uuid.uuid4)
    plan = 'free'
    status = 'active'