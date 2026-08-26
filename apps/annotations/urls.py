from rest_framework.routers import DefaultRouter
from .views import AnnotationViewSet

router = DefaultRouter()
router.register(r'annotations', AnnotationViewSet, basename='annotation')

urlpatterns = router.urls