from rest_framework.routers import DefaultRouter
from .views import UserModelViewSet

router = DefaultRouter()
router.register(r'users', UserModelViewSet)

urlpatterns = router.urls
