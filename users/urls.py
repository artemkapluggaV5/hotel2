from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegisterViewSet, UserInfoView # Добавили импорт

router = DefaultRouter()
router.register(r'register', RegisterViewSet, basename='register')

urlpatterns = [
    # ПУТЬ 'me/' ДОЛЖЕН БЫТЬ ПЕРЕД ROUTER.URLS
    path('me/', UserInfoView.as_view(), name='user-info'),
    path('', include(router.urls)),
]