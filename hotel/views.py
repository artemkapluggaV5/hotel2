from django.utils import timezone
from django.db.models import Q
from rest_framework import viewsets, mixins, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError  # Добавили для ошибок
from .models import *
from .serializers import *
from .permissions import IsAdmin, IsStaffOrAdmin, IsGuest


class RegisterViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsAdmin()]


class RoomViewSet(viewsets.ModelViewSet):
    serializer_class = RoomSerializer
    queryset = Room.objects.all()

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsAdmin()]

    def get_queryset(self):
        queryset = Room.objects.all()

        # Фильтры по датам
        check_in = self.request.query_params.get('check_in')
        check_out = self.request.query_params.get('check_out')

        # Желательные требования из ТЗ: Фильтры по категории и стоимости
        category_id = self.request.query_params.get('category')
        max_price = self.request.query_params.get('max_price')

        if category_id:
            queryset = queryset.filter(category_id=category_id)

        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        if check_in and check_out:
            busy_rooms = Placement.objects.filter(
                Q(check_in_date__lt=check_out) & Q(check_out_date__gt=check_in),
                status__in=['waiting', 'active']
            ).values_list('room_id', flat=True)

            queryset = queryset.exclude(id__in=busy_rooms).filter(status='available')

        return queryset

    @action(detail=True, methods=['post'], permission_classes=[IsStaffOrAdmin])
    def finish_cleaning(self, request, pk=None):
        room = self.get_object()
        if room.status == 'maintenance':
            room.status = 'available'
            room.save()
            return Response({"status": "Room is now available."})
        return Response({"error": "Room is not in maintenance mode."}, status=400)


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsStaffOrAdmin]


class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.profile.role in ['admin', 'staff']:
            return Booking.objects.all()
        return Booking.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PlacementViewSet(viewsets.ModelViewSet):
    queryset = Placement.objects.all()
    serializer_class = PlacementSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsStaffOrAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        if self.request.user.profile.role in ['admin', 'staff']:
            return Placement.objects.all()
        return Placement.objects.filter(booking__user=self.request.user)

    def perform_create(self, serializer):
        room = serializer.validated_data['room']
        check_in = serializer.validated_data['check_in_date']
        check_out = serializer.validated_data['check_out_date']

        days = (check_out - check_in).days
        price_per_night = room.price

        placement = serializer.save(price_per_night=price_per_night)

        booking = placement.booking
        booking.total_price += (days * price_per_night)
        booking.save()

    def perform_update(self, serializer):
        status_before = self.get_object().status
        status_after = serializer.validated_data.get('status', status_before)
        booking = self.get_object().booking

        if status_before == 'waiting' and status_after == 'active':
            if booking.status != 'confirmed':
                raise ValidationError({"error": "Заселение невозможно: бронирование не подтверждено."})

        placement = serializer.save()

        if placement.status == 'active' and not placement.check_in_fact:
            placement.check_in_fact = timezone.now()
            placement.room.status = 'occupied'
            placement.room.save()

        if placement.status == 'finished' and not placement.check_out_fact:
            placement.check_out_fact = timezone.now()
            placement.room.status = 'maintenance'
            placement.room.save()

        placement.save()


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.profile.role in ['admin', 'staff']:
            return Payment.objects.all()
        return Payment.objects.filter(booking__user=self.request.user)


class GuestViewSet(viewsets.ModelViewSet):
    queryset = Guest.objects.all()
    serializer_class = GuestSerializer
    permission_classes = [IsStaffOrAdmin]