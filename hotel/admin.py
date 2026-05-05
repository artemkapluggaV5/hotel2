from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import Category, Room, Booking, Payment, Placement, Guest, Profile

admin.site.register(Category)
admin.site.register(Room)
admin.site.register(Booking)
admin.site.register(Payment)
admin.site.register(Placement)
admin.site.register(Guest)
admin.site.register(Profile)