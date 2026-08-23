from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AIAssistViewSet

router = DefaultRouter()
router.register(r'ai', AIAssistViewSet, basename='ai')

urlpatterns = [
    path('', include(router.urls)),
]