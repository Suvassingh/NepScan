from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IDCardViewSet

router = DefaultRouter()
router.register(r'id-card', IDCardViewSet, basename='id-card')

urlpatterns = [
    path('', include(router.urls)),
]