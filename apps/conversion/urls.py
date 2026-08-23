from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ConversionViewSet

router = DefaultRouter()
router.register(r'export', ConversionViewSet, basename='export')

urlpatterns = [
    path('', include(router.urls)),
]