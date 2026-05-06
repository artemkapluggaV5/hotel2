from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .views import (
    CategoryViewSet,
    RoomViewSet,
    ProfileViewSet,
    BookingViewSet,
    PlacementViewSet,
    PaymentViewSet,
    GuestViewSet, RegisterViewSet,
)

router = DefaultRouter()

router.register(r'categories', CategoryViewSet)
router.register(r'rooms', RoomViewSet)
router.register(r'profiles', ProfileViewSet)
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'placements', PlacementViewSet, basename='placement')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'register', RegisterViewSet, basename='register')
router.register(r'guests', GuestViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]