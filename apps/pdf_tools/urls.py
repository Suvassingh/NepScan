from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PDFToolsViewSet

router = DefaultRouter()
router.register(r'pdf', PDFToolsViewSet, basename='pdf')

urlpatterns = [
    path('', include(router.urls)),
]