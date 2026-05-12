from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
class User(AbstractUser):
    ROLE_CHOICES = [
        ('guest', 'Guest'),
        ('admin', 'Admin'),
        ('staff', 'Staff'),
    ]
    phone = models.CharField(max_length=20, blank=True, null=True)
    passport_data = models.CharField(max_length=100, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='guest')

    def __str__(self):
        return self.username