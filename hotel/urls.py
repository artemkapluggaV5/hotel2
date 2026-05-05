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
    GuestViewSet,
)

router = DefaultRouter()

router.register(r'categories', CategoryViewSet)
router.register(r'rooms', RoomViewSet)
router.register(r'profiles', ProfileViewSet)
router.register(r'bookings', BookingViewSet)
router.register(r'placements', PlacementViewSet)
router.register(r'payments', PaymentViewSet)
router.register(r'guests', GuestViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]