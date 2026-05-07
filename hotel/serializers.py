from rest_framework import serializers
from django.contrib.auth.models import User

from .models import *


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


class ProfileSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Profile
        fields = '__all__'


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
        if data['check_out_date'] <= data['check_in_date']:
            raise serializers.ValidationError("Check-out date must be after check-in date.")
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


class RegisterSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'phone']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        phone = validated_data.pop('phone')
        password = validated_data.pop('password')

        user = User.objects.create_user(
            password=password,
            **validated_data
        )

        user.profile.phone = phone
        user.profile.save()

        return user