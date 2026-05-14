from django.contrib import admin
from django.db import models
from image_uploader_widget.widgets import ImageUploaderWidget
from django.contrib.auth.admin import UserAdmin
from .models import User, Category, Room, Booking, Payment, Placement, Guest

admin.site.register(Category)
admin.site.register(Booking)
admin.site.register(Payment)
admin.site.register(Placement)
admin.site.register(Guest)


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_number', 'category', 'price', 'status')

    formfield_overrides = {
        models.ImageField: {'widget': ImageUploaderWidget},
    }