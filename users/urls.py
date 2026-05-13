from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegisterViewSet, UserInfoView # Добавили импорт

router = DefaultRouter()
router.register(r'register', RegisterViewSet, basename='register')

urlpatterns = [
    path('me/', UserInfoView.as_view(), name='user-info'),
    path('', include(router.urls)),
]