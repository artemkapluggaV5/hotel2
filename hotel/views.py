from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from rest_framework import viewsets, mixins, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from yookassa import Configuration, Payment as YooPayment
from .telegram import send_telegram_message
from django.contrib.auth import get_user_model
from .models import *
import uuid
from .serializers import *
from .permissions import IsAdmin, IsStaffOrAdmin, IsGuest
from rest_framework.views import APIView

User = get_user_model()

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
        check_in = self.request.query_params.get('check_in')
        check_out = self.request.query_params.get('check_out')
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

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and hasattr(user, 'role'):
            if user.role in ['admin', 'staff'] and self.request.query_params.get('all') == 'true':
                return Booking.objects.all()
            return Booking.objects.filter(user=user)
        return Booking.objects.none()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        status_before = self.get_object().status
        booking = serializer.save()

        if status_before == 'pending' and booking.status == 'canceled':
            for placement in booking.placements.all():
                placement.status = 'canceled'
                placement.save()

            pending_payments = Payment.objects.filter(booking=booking, status='pending')
            for payment in pending_payments:
                try:
                    if payment.yookassa_payment_id:
                        YooPayment.cancel(payment.yookassa_payment_id)
                    payment.status = 'canceled'
                    payment.save()
                except Exception as e:
                    print(f"Ошибка отмены в ЮKassa: {e}")


class PlacementViewSet(viewsets.ModelViewSet):
    queryset = Placement.objects.all()
    serializer_class = PlacementSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated()]
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsStaffOrAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            return Placement.objects.none()

        if user.role in ['admin', 'staff']:
            return Placement.objects.all()

        return Placement.objects.filter(booking__user=user)

    def partial_update(self, request, *args, **kwargs):
        print("PATCH CALLED")
        print("PK =", kwargs.get("pk"))
        print("USER =", request.user)

        return super().partial_update(request, *args, **kwargs)

    def perform_update(self, serializer):
        status_before = self.get_object().status
        booking = self.get_object().booking

        if status_before == 'waiting' and serializer.validated_data.get('status') == 'active':
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
        if self.request.user.role in ['admin', 'staff']:
            return Payment.objects.all()
        return Payment.objects.filter(booking__user=self.request.user)

class GuestViewSet(viewsets.ModelViewSet):
    queryset = Guest.objects.all()
    serializer_class = GuestSerializer
    permission_classes = [IsStaffOrAdmin]


class HotelStatsView(APIView):
    permission_classes = [IsStaffOrAdmin]

    def get(self, request):
        total_rooms = Room.objects.count()
        available_rooms = Room.objects.filter(status='available').count()
        occupied_rooms = Room.objects.filter(status='occupied').count()
        maintenance_rooms = Room.objects.filter(status='maintenance').count()

        total_revenue = Booking.objects.filter(status='confirmed').aggregate(models.Sum('total_price'))['total_price__sum'] or 0

        return Response({
            "total_rooms": total_rooms,
            "available_rooms": available_rooms,
            "occupied_rooms": occupied_rooms,
            "maintenance_rooms": maintenance_rooms,
            "total_revenue": total_revenue
        })


Configuration.account_id = settings.YOOKASSA_SHOP_ID
Configuration.secret_key = settings.YOOKASSA_SECRET_KEY


class CreateYooKassaPaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        booking_id = request.data.get('booking_id')
        frontend_url = request.data.get('return_url', 'http://localhost:5173')

        try:
            booking = Booking.objects.get(id=booking_id, user=request.user, status='pending')

            calculated_price = sum(
                placement.room.price
                for placement in booking.placements.all()
            )

            booking.total_price = calculated_price
            booking.save()

            if booking.total_price <= 0:
                return Response({"error": "Сумма бронирования не может быть 0. Добавьте номера."},
                                status=status.HTTP_400_BAD_REQUEST)

        except Booking.DoesNotExist:
            return Response({"error": "Бронь не найдена"}, status=404)

        with transaction.atomic():
            idempotence_key = str(uuid.uuid4())

            yookassa_payment = YooPayment.create({
                "amount": {"value": str(booking.total_price), "currency": "RUB"},
                "confirmation": {
                    "type": "redirect",
                    "return_url": f"{frontend_url}/account"
                },
                "capture": True,
                "description": f"Оплата бронирования №{booking.id}"
            }, idempotence_key)

            Payment.objects.create(
                booking=booking,
                amount=booking.total_price,
                yookassa_payment_id=yookassa_payment.id,
                status='pending'
            )

        return Response({"confirmation_url": yookassa_payment.confirmation.confirmation_url})

class CheckPaymentStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        booking_id = request.data.get('booking_id')

        with transaction.atomic():
            payments = Payment.objects.select_for_update().filter(
                booking__id=booking_id,
                status='pending'
            ).order_by('-id')

            if not payments.exists():
                return Response({"message": "Нет ожидающих платежей для этой брони."})

            payment = payments.first()

            try:
                yookassa_payment = YooPayment.find_one(payment.yookassa_payment_id)
            except Exception as e:
                print(f"Ошибка связи с ЮKassa: {e}")
                return Response({"error": "Ошибка связи"}, status=500)

            if yookassa_payment.status == 'succeeded':
                payment.status = 'paid'
                payment.save()

                payments.exclude(id=payment.id).update(status='canceled')

                booking = payment.booking
                booking.status = 'confirmed'
                booking.save()

                rooms_info = [f"№{p.room.room_number} ({p.room.category.name})" for p in booking.placements.all()]
                rooms_text = ", ".join(rooms_info)
                user = booking.user
                if user.telegram_id:
                    msg = (
                        f"🎉 <b>Оплата прошла успешно!</b>\n\n"
                        f"🏨 Бронирование <b>№{booking.id}</b> подтверждено.\n"
                        f"🛏 <b>Номер:</b> {rooms_text}\n" 
                        f"💰 Оплачено: {payment.amount} ₽"
                    )
                    send_telegram_message(user.telegram_id, msg)

                return Response({"status": "success", "message": "Оплата прошла успешно!"})

            elif yookassa_payment.status == 'canceled':
                payment.status = 'canceled'
                payment.save()
                return Response({"status": "canceled", "message": "Платеж отменен"})

            return Response({"status": "pending", "message": "Оплата еще не поступила"})