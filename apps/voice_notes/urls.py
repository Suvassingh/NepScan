from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VoiceNoteViewSet

router = DefaultRouter()
router.register(r'voice', VoiceNoteViewSet, basename='voice')

urlpatterns = [
    path('', include(router.urls)),
]