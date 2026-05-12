from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()

router.register(r'categories', CategoryViewSet)
router.register(r'rooms', RoomViewSet, basename='room')
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'placements', PlacementViewSet, basename='placement')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'guests', GuestViewSet)

urlpatterns = [
    path('', include(router.urls)),
]