from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from collections import Counter

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser

from common.supabase_client import get_supabase_client
from apps.ocr.models import OCRJob
from apps.audit.models import AuditLogEntry
from apps.billing.models import Subscription
from apps.workspaces.models import Organization

 
@staff_member_required
def dashboard(request):
    supabase = get_supabase_client()

    profiles_resp = supabase.table('profiles').select('id', count='exact').execute()
    total_users = profiles_resp.count or 0

    docs_resp = supabase.table('documents').select('id', count='exact').execute()
    total_docs = docs_resp.count or 0

    pages_resp = supabase.table('pages').select('id', count='exact').execute()
    total_pages = pages_resp.count or 0

    storage_resp = supabase.table('documents').select('file_size_bytes').execute()
    total_storage = sum(doc.get('file_size_bytes', 0) for doc in storage_resp.data) if storage_resp.data else 0

    ocr_done = OCRJob.objects.filter(status='done').count()
    ocr_failed = OCRJob.objects.filter(status='failed').count()
    ocr_pending = OCRJob.objects.filter(status__in=['queued', 'running']).count()

    total_orgs = Organization.objects.count()
    total_subs = Subscription.objects.count()
    pro_subs = Subscription.objects.filter(plan__startswith='pro').count()

    recent_activities = AuditLogEntry.objects.order_by('-created_at')[:10]

    today = timezone.now().date()
    window_start_date = today - timedelta(days=6)
    window_start = timezone.make_aware(
        timezone.datetime.combine(window_start_date, timezone.datetime.min.time())
    )

    labels = [(window_start_date + timedelta(days=i)).strftime('%d/%m') for i in range(7)]

    def bucket_by_day(rows):
        counts = Counter()
        for row in rows or []:
            created = row.get('created_at')
            if not created:
                continue
            day = timezone.datetime.fromisoformat(created.replace('Z', '+00:00')).date()
            counts[day] += 1
        return counts

    profiles_in_range = supabase.table('profiles').select('created_at') \
        .gte('created_at', window_start.isoformat()).execute()
    docs_in_range = supabase.table('documents').select('created_at') \
        .gte('created_at', window_start.isoformat()).execute()

    user_counts_by_day = bucket_by_day(profiles_in_range.data)
    doc_counts_by_day = bucket_by_day(docs_in_range.data)

    user_data = [user_counts_by_day.get(window_start_date + timedelta(days=i), 0) for i in range(7)]
    doc_data = [doc_counts_by_day.get(window_start_date + timedelta(days=i), 0) for i in range(7)]

    context = {
        'total_users': total_users,
        'total_documents': total_docs,
        'total_pages': total_pages,
        'total_storage_bytes': total_storage,
        'ocr_done': ocr_done,
        'ocr_failed': ocr_failed,
        'ocr_pending': ocr_pending,
        'total_organizations': total_orgs,
        'total_subscriptions': total_subs,
        'pro_subscriptions': pro_subs,
        'recent_activities': recent_activities,
        'chart_labels': labels,
        'user_chart_data': user_data,
        'doc_chart_data': doc_data,
    }
    return render(request, 'admin/dashboard.html', context)

 
class AdminMetricsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        supabase = get_supabase_client()

        profiles_resp = supabase.table('profiles').select('id', count='exact').execute()
        total_users = profiles_resp.count or 0

        docs_resp = supabase.table('documents').select('id', count='exact').execute()
        total_docs = docs_resp.count or 0

        storage_resp = supabase.table('documents').select('file_size_bytes').execute()
        total_storage = sum(doc.get('file_size_bytes', 0) for doc in storage_resp.data) if storage_resp.data else 0

        total_ocr_jobs = OCRJob.objects.count()
        ocr_done = OCRJob.objects.filter(status='done').count()
        ocr_failed = OCRJob.objects.filter(status='failed').count()

        total_orgs = Organization.objects.count()
        total_subscriptions = Subscription.objects.count()
        pro_subscriptions = Subscription.objects.filter(plan__startswith='pro').count()

        recent_activities = AuditLogEntry.objects.order_by('-created_at')[:10].values('event_type', 'actor_id', 'created_at')

        return Response({
            'total_users': total_users,
            'total_documents': total_docs,
            'total_storage_bytes': total_storage,
            'total_ocr_jobs': total_ocr_jobs,
            'ocr_done': ocr_done,
            'ocr_failed': ocr_failed,
            'total_organizations': total_orgs,
            'total_subscriptions': total_subscriptions,
            'pro_subscriptions': pro_subscriptions,
            'recent_activities': list(recent_activities),
        })