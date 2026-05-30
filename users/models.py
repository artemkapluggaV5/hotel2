from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


# Create your models here.


class CustomUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        # Жестко говорим: если создается суперюзер, его роль ВСЕГДА 'admin'
        extra_fields.setdefault('role', 'admin')
        return super().create_superuser(username, email, password, **extra_fields)

class User(AbstractUser):
    ROLE_CHOICES = [('guest', 'Guest'), ('admin', 'Admin'), ('staff', 'Staff')]

    email = models.EmailField(unique=True, verbose_name='Почта')
    phone = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name='Телефон')

    full_name = models.CharField(max_length=150, blank=True, null=True, verbose_name='ФИО')
    passport_data = models.CharField(max_length=100, blank=True, null=True, verbose_name='Паспортные данные')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='guest', verbose_name='Роль')
    verification_code = models.CharField(max_length=6, blank=True, null=True)
    telegram_id = models.CharField(max_length=50, blank=True, null=True, verbose_name='Telegram ID')


    objects = CustomUserManager()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username