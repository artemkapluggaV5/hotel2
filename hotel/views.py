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
        if user.role in ['admin', 'staff'] and self.request.query_params.get('all') == 'true':
            return Booking.objects.all()
        return Booking.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class PlacementViewSet(viewsets.ModelViewSet):
    queryset = Placement.objects.all()
    serializer_class = PlacementSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.role in ['admin', 'staff'] and self.request.query_params.get('all') == 'true':
            return Placement.objects.all()

        return Placement.objects.filter(booking__user=user)

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

        total_revenue = Booking.objects.filter(status='confirmed').aggregate(models.Sum('total_price'))[
                            'total_price__sum'] or 0

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
        try:
            booking = Booking.objects.get(id=booking_id, user=request.user, status='pending')
        except Booking.DoesNotExist:
            return Response({"error": "Бронь не найдена или уже оплачена"}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            idempotence_key = str(uuid.uuid4())

            yookassa_payment = YooPayment.create({
                "amount": {
                    "value": str(booking.total_price),
                    "currency": "RUB"
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": "http://localhost:5173/account"
                },
                "capture": True,
                "description": f"Оплата бронирования №{booking.id} в OASIS Hotel"
            }, idempotence_key)

            our_payment = Payment.objects.create(
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
            try:
                payment = Payment.objects.select_for_update().get(booking__id=booking_id, status='pending')
            except Payment.DoesNotExist:
                return Response({"message": "Оплата уже обработана другим запросом."})

            try:
                yookassa_payment = YooPayment.find_one(payment.yookassa_payment_id)
            except Exception as e:
                print(f"Ошибка связи с ЮKassa: {e}")
                return Response({"error": "Ошибка связи"}, status=500)

            if yookassa_payment.status == 'succeeded':
                payment.status = 'paid'
                payment.save()

                booking = payment.booking
                booking.status = 'confirmed'
                booking.save()

                rooms_info = []
                for placement in booking.placements.all():
                    rooms_info.append(f"№{placement.room.room_number} ({placement.room.category.name})")

                rooms_text = ", ".join(rooms_info) if rooms_info else "Не назначен"

                user = booking.user
                if user.telegram_id:
                    msg = (
                        f"🎉 <b>Оплата прошла успешно!</b>\n\n"
                        f"🏨 Бронирование <b>№{booking.id}</b> подтверждено.\n"
                        f"🛏 <b>Номер:</b> {rooms_text}\n" 
                        f"📅 Заезд: {booking.check_in_date}\n"
                        f"📅 Выезд: {booking.check_out_date}\n"
                        f"💰 Оплачено: {payment.amount} ₽\n\n"
                        f"Ждем вас в OASIS Hotel!"
                    )
                    send_telegram_message(user.telegram_id, msg)

                return Response({"status": "success", "message": "Оплата прошла успешно!"})

            elif yookassa_payment.status == 'canceled':
                payment.status = 'canceled'
                payment.save()
                return Response({"status": "canceled", "message": "Платеж отменен"})

            return Response({"status": "pending", "message": "Оплата еще не поступила"})