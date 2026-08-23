from django.contrib import admin
from unfold.admin import ModelAdmin  # <-- works with Unfold
from apps.audit.models import AuditLogEntry
from apps.ocr.models import OCRJob, OCRResult
from apps.expense.models import ExpenseData
from apps.billing.models import Subscription
from apps.workspaces.models import Organization, OrganizationMembership
from apps.supabase_models.models import (
    Document, Folder, Page, Tag, DocumentTag, Profile, DocumentShare
)
 
@admin.register(AuditLogEntry)
class AuditLogEntryAdmin(ModelAdmin):
    list_display = ['id', 'event_type', 'actor_id', 'target_id', 'created_at']
    readonly_fields = [f.name for f in AuditLogEntry._meta.get_fields()]

@admin.register(OCRJob)
class OCRJobAdmin(ModelAdmin):
    list_display = ['id', 'document_id', 'job_type', 'status', 'created_at']
    list_filter = ['status', 'job_type']
    readonly_fields = ['id', 'created_at', 'completed_at']

@admin.register(OCRResult)
class OCRResultAdmin(ModelAdmin):
    list_display = ['document_id', 'detected_language', 'confidence', 'created_at']
    readonly_fields = ['id', 'created_at']

@admin.register(ExpenseData)
class ExpenseDataAdmin(ModelAdmin):
    list_display = ['document_id', 'expense_date', 'category', 'amount', 'currency']
    readonly_fields = ['id']

@admin.register(Subscription)
class SubscriptionAdmin(ModelAdmin):
    list_display = ['owner_id', 'plan', 'status', 'current_period_end']

@admin.register(Document)
class DocumentAdmin(ModelAdmin):
    list_display = ['id', 'title', 'owner_id', 'created_at']
    search_fields = ['title', 'owner_id']
    readonly_fields = ['id', 'created_at', 'updated_at']

@admin.register(Folder)
class FolderAdmin(ModelAdmin):
    list_display = ['id', 'name', 'owner_id', 'created_at']
    search_fields = ['name']

@admin.register(Page)
class PageAdmin(ModelAdmin):
    list_display = ['id', 'document_id', 'page_number', 'filter_applied']
    list_filter = ['filter_applied']

@admin.register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ['id', 'name', 'owner_id']
    search_fields = ['name']

@admin.register(DocumentTag)
class DocumentTagAdmin(ModelAdmin):
    list_display = ['document_id', 'tag_id']

@admin.register(Profile)
class ProfileAdmin(ModelAdmin):
    list_display = ['id', 'full_name', 'plan', 'created_at']
    search_fields = ['full_name']
    readonly_fields = ['id', 'created_at']

@admin.register(DocumentShare)
class DocumentShareAdmin(ModelAdmin):
    list_display = ['document_id', 'owner_id', 'shared_with_id', 'permission', 'expires_at']
    search_fields = ['share_token']

@admin.register(Organization)
class OrganizationAdmin(ModelAdmin):
    list_display = ['id', 'name', 'created_at']

@admin.register(OrganizationMembership)
class OrganizationMembershipAdmin(ModelAdmin):
    list_display = ['id', 'organization', 'user_id', 'role', 'joined_at']