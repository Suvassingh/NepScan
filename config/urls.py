from django.contrib import admin
from django.urls import path, include
from apps.admin_panel.views import dashboard
from apps.billing.views import share_preview, share_download
from apps.image_processing.views import CorrectPerspectiveView

urlpatterns = [ 
    path('admin/dashboard/', dashboard, name='admin_dashboard'),   
    path('admin/', admin.site.urls),
    path('api/v1/', include('apps.ocr.urls')),
    path('api/v1/', include('apps.pdf_tools.urls')),
    path('api/v1/', include('apps.ai_assist.urls')),
    path('api/v1/', include('apps.expense.urls')),
    path('api/v1/', include('apps.conversion.urls')),
    path('api/v1/', include('apps.id_card.urls')),
    path('api/v1/', include('apps.jobs.urls')),
    path('api/v1/', include('apps.billing.urls')),
    path('api/v1/', include('apps.voice_notes.urls')),
    path('api/v1/', include('apps.workspaces.urls')),
    path('api/v1/admin/', include('apps.admin_panel.urls')),
    path('share/<str:token>/', share_preview, name='share_preview'),
    path('share/<str:token>/download/', share_download, name='share_download'),
    path('api/v1/image/correct-perspective/', CorrectPerspectiveView.as_view(), name='correct_perspective'),
    path('api/v1/', include('apps.annotations.urls')),


]