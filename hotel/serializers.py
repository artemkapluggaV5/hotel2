from rest_framework import serializers
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from .models import *

User = get_user_model()

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class RoomSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())

    class Meta:
        model = Room
        fields = [
            'id', 'room_number', 'category', 'price',
            'amenities', 'features', 'description',
            'rating', 'rules', 'status'
        ]


class BookingSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'user',
            'check_in_date', 'check_out_date',
            'status', 'booking_date', 'total_price'
        ]
        read_only_fields = ['booking_date', 'total_price']

    def validate(self, data):
        # 1. Берем новые даты из запроса, если они есть.
        # Если их нет (как при PATCH), берем старые даты из существующей записи (self.instance)
        check_in = data.get('check_in_date')
        check_out = data.get('check_out_date')

        if self.instance:
            if not check_in:
                check_in = self.instance.check_in_date
            if not check_out:
                check_out = self.instance.check_out_date

        # 2. Проверяем даты только если обе даты у нас на руках
        if check_in and check_out:
            if check_out <= check_in:
                raise serializers.ValidationError("Дата выезда должна быть позже даты заезда.")

        return data

class PlacementSerializer(serializers.ModelSerializer):
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all())
    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all())

    class Meta:
        model = Placement
        fields = '__all__'
        read_only_fields = ['price_per_night']

    def validate(self, data):
        room = data['room']
        check_in = data['check_in_date']
        check_out = data['check_out_date']

        overlapping = Placement.objects.filter(
            room=room,
            check_in_date__lt=check_out,
            check_out_date__gt=check_in,
            status__in=['waiting', 'active']
        )
        if self.instance:
            overlapping = overlapping.exclude(id=self.instance.id)

        if overlapping.exists():
            raise serializers.ValidationError({"room": "Room is already booked for these dates."})

        return data

class PaymentSerializer(serializers.ModelSerializer):
    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all())

    class Meta:
        model = Payment
        fields = '__all__'

class GuestSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    placement = serializers.PrimaryKeyRelatedField(queryset=Placement.objects.all())

    class Meta:
        model = Guest
        fields = '__all__'