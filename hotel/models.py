from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    ROLE_CHOICES = [
        ('guest', 'Guest'),
        ('admin', 'Admin'),
        ('staff', 'Staff'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20)
    passport_data = models.CharField(max_length=100, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='guest')

    def __str__(self):
        return self.user.username

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    max_guests = models.PositiveIntegerField()
    base_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

class Room(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('maintenance', 'Maintenance'),
    ]
    room_number = models.CharField(max_length=10, unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='rooms')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    amenities = models.TextField(blank=True, null=True)
    features = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    rules = models.TextField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='available')

    def __str__(self):
        return self.room_number

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('canceled', 'Canceled'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    booking_date = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0) # Добавил default=0

    def __str__(self):
        return f"Booking #{self.id}"

class Placement(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'Waiting'),
        ('active', 'Active'),
        ('finished', 'Finished'),
    ]
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='placements')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='placements')
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    guests_count = models.PositiveIntegerField()
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    check_in_fact = models.DateTimeField(null=True, blank=True)
    check_out_fact = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='waiting')

    def __str__(self):
        return f"{self.room} ({self.booking.id})"

class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_type = models.CharField(max_length=50)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Payment #{self.id}"

class Guest(models.Model):
    placement = models.ForeignKey(Placement, on_delete=models.CASCADE, related_name='guests')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='guest_records')
    is_primary = models.BooleanField(default=False)
    check_in_at = models.DateTimeField(null=True, blank=True)
    special_requests = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.user.username