from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
class User(AbstractUser):
    ROLE_CHOICES = [('guest', 'Guest'), ('admin', 'Admin'), ('staff', 'Staff')]

    # Сделали email и phone обязательными для уникальности
    email = models.EmailField(unique=True, verbose_name='Почта')
    phone = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name='Телефон')

    full_name = models.CharField(max_length=150, blank=True, null=True, verbose_name='ФИО')
    passport_data = models.CharField(max_length=100, blank=True, null=True, verbose_name='Паспортные данные')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='guest', verbose_name='Роль')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username