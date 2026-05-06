from django.contrib import admin
from .models import *

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone')
    list_filter = ('role',)

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_number', 'category', 'price', 'status')
    list_filter = ('status', 'category')
    search_fields = ('room_number',)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'check_in_date', 'check_out_date', 'status', 'total_price')
    list_filter = ('status', 'check_in_date')

@admin.register(Placement)
class PlacementAdmin(admin.ModelAdmin):
    list_display = ('booking', 'room', 'check_in_date', 'check_out_date', 'status')
    list_filter = ('status',)

admin.site.register(Category)
admin.site.register(Payment)
admin.site.register(Guest)