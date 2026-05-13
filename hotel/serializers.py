from rest_framework import serializers
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from .models import *
from datetime import date

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
        check_in = data.get('check_in_date')
        check_out = data.get('check_out_date')
        today = date.today()

        if self.instance:
            if not check_in:
                check_in = self.instance.check_in_date
            if not check_out:
                check_out = self.instance.check_out_date

        if not self.instance and check_in and check_in < today:
            raise serializers.ValidationError({"check_in_date": "Нельзя забронировать номер на прошедшую дату."})

        if check_in and check_out:
            if check_out <= check_in:
                raise serializers.ValidationError({"check_out_date": "Дата выезда должна быть позже даты заезда."})

        return data

class PlacementSerializer(serializers.ModelSerializer):
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all())
    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all())

    class Meta:
        model = Placement
        fields = '__all__'
        read_only_fields = ['price_per_night']

    def validate(self, data):
        room = data.get('room')
        check_in = data.get('check_in_date')
        check_out = data.get('check_out_date')
        today = date.today()

        # Если PATCH запрос
        if self.instance:
            room = room or self.instance.room
            check_in = check_in or self.instance.check_in_date
            check_out = check_out or self.instance.check_out_date

        if not self.instance and check_in and check_in < today:
            raise serializers.ValidationError({"check_in_date": "Дата заезда не может быть в прошлом."})

        overlapping = Placement.objects.filter(
            room=room,
            check_in_date__lt=check_out,
            check_out_date__gt=check_in,
            status__in=['waiting', 'active']
        )
        if self.instance:
            overlapping = overlapping.exclude(id=self.instance.id)

        if overlapping.exists():
            raise serializers.ValidationError({"room": "Этот номер уже забронирован на выбранные даты."})

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