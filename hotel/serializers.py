from rest_framework import serializers, viewsets
from .models import *
from django.contrib.auth.models import User


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class RoomSerializer(serializers.ModelSerializer):
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category'
    )

    class Meta:
        model = Room
        fields = [
            'id', 'room_number', 'category_id', 'price',
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


class PlacementSerializer(serializers.ModelSerializer):
    room_id = serializers.PrimaryKeyRelatedField(
        queryset=Room.objects.all(),
        source='room'
    )
    booking_id = serializers.PrimaryKeyRelatedField(
        queryset=Booking.objects.all(),
        source='booking'
    )

    class Meta:
        model = Placement
        fields = '__all__'


class PaymentSerializer(serializers.ModelSerializer):
    booking_id = serializers.PrimaryKeyRelatedField(
        queryset=Booking.objects.all(),
        source='booking'
    )

    class Meta:
        model = Payment
        fields = '__all__'


class GuestSerializer(serializers.ModelSerializer):
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user'
    )
    placement_id = serializers.PrimaryKeyRelatedField(
        queryset=Placement.objects.all(),
        source='placement'
    )

    class Meta:
        model = Guest
        fields = '__all__'

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class RegisterViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer