from django.urls import path
from .views import SharingViewSet, BillingViewSet

urlpatterns = [
    path('shares/share_document/', SharingViewSet.as_view({'post': 'share_document'}), name='share_document'),
    path('shares/shared_with_me/', SharingViewSet.as_view({'get': 'shared_with_me'}), name='shared_with_me'),
    path('shares/generate_share_link/', SharingViewSet.as_view({'post': 'generate_share_link'}), name='generate_share_link'),
    path('webhooks/status/', BillingViewSet.as_view({'get': 'status'}), name='billing_status'),
    path('webhooks/webhook/', BillingViewSet.as_view({'post': 'webhook'}), name='billing_webhook'),
]