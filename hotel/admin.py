from django.contrib import admin
from django.db import models
from image_uploader_widget.widgets import ImageUploaderWidget
from .models import Category, Room, Booking, Payment, Placement, Guest


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_price', 'max_guests')


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_number', 'status', 'category', 'price')
    list_filter = ('status', 'category')
    fields = ('status', 'room_number', 'category', 'price', 'image', 'amenities', 'features', 'description', 'rating',
              'rules')

    formfield_overrides = {
        models.ImageField: {'widget': ImageUploaderWidget},
    }


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'user', 'check_in_date', 'check_out_date', 'total_price')
    list_filter = ('status',)
    fields = ('status', 'user', 'check_in_date', 'check_out_date', 'total_price')


@admin.register(Placement)
class PlacementAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'booking', 'room', 'check_in_date', 'check_out_date')
    list_filter = ('status',)
    fields = ('status', 'booking', 'room', 'check_in_date', 'check_out_date', 'guests_count', 'price_per_night',
              'check_in_fact', 'check_out_fact')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'booking', 'amount', 'payment_type')
    list_filter = ('status', 'payment_type')
    fields = ('status', 'booking', 'amount', 'payment_type')


@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display = ('user', 'placement', 'is_primary')