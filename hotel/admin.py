from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Category, Room, Booking, Payment, Placement, Guest

admin.site.register(Category)
admin.site.register(Room)
admin.site.register(Booking)
admin.site.register(Payment)
admin.site.register(Placement)
admin.site.register(Guest)