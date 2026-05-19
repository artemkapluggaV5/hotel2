from django.db import models
from django.conf import settings
from autoslug import AutoSlugField

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name='Название категории')
    slug = AutoSlugField(populate_from='name', unique=True, always_update=True, verbose_name='URL (Слаг)')
    description = models.CharField(max_length=255, blank=True, null=True, verbose_name='Описание')
    max_guests = models.PositiveIntegerField(verbose_name='Макс. гостей')
    base_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Базовая цена')

    class Meta:
        verbose_name = 'Категория номера'
        verbose_name_plural = 'Категории номеров'

    def __str__(self):
        return self.name

class Room(models.Model):
    STATUS_CHOICES = [
        ('available', 'Свободен'),
        ('occupied', 'Занят'),
        ('maintenance', 'На уборке/ремонте'),
    ]
    room_number = models.CharField(max_length=10, unique=True, verbose_name='Номер комнаты')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='rooms', verbose_name='Категория')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена за сутки')
    image = models.ImageField(upload_to='rooms/', null=True, blank=True, verbose_name="Изображение номера")
    amenities = models.TextField(blank=True, null=True, verbose_name='Удобства')
    features = models.CharField(max_length=255, blank=True, null=True, verbose_name='Особенности')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True, verbose_name='Рейтинг')
    rules = models.TextField(verbose_name='Правила проживания')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='available', verbose_name='Статус')

    class Meta:
        verbose_name = 'Номер'
        verbose_name_plural = 'Номерной фонд'

    def __str__(self):
        return self.room_number

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает оплаты'),
        ('confirmed', 'Подтверждено (Оплачено)'),
        ('canceled', 'Отменено'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings', verbose_name='Клиент')
    check_in_date = models.DateField(verbose_name='Дата заезда')
    check_out_date = models.DateField(verbose_name='Дата выезда')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending', verbose_name='Статус')
    booking_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания брони')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Итоговая стоимость')

    class Meta:
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'

    def __str__(self):
        return f"Бронь #{self.id} ({self.user.username})"

class Placement(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'Ожидает заезда'),
        ('active', 'Проживает'),
        ('finished', 'Выехал'),
    ]
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='placements', verbose_name='Бронь')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='placements', verbose_name='Номер')
    check_in_date = models.DateField(verbose_name='План. заезд')
    check_out_date = models.DateField(verbose_name='План. выезд')
    guests_count = models.PositiveIntegerField(verbose_name='Кол-во гостей')
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Цена за ночь (фикс.)')
    check_in_fact = models.DateTimeField(null=True, blank=True, verbose_name='Фактический заезд')
    check_out_fact = models.DateTimeField(null=True, blank=True, verbose_name='Фактический выезд')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='waiting', verbose_name='Статус')

    class Meta:
        verbose_name = 'Размещение'
        verbose_name_plural = 'Размещения'

    def __str__(self):
        return f"Размещение в {self.room} по брони #{self.booking.id}"

class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидание'),
        ('paid', 'Оплачено'),
        ('failed', 'Ошибка'),
    ]
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payments', verbose_name='Бронь')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сумма')
    payment_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата оплаты')
    payment_type = models.CharField(max_length=50, verbose_name='Способ оплаты')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending', verbose_name='Статус')

    class Meta:
        verbose_name = 'Оплата'
        verbose_name_plural = 'Оплаты'

    def __str__(self):
        return f"Оплата #{self.id}"

class Guest(models.Model):
    placement = models.ForeignKey(Placement, on_delete=models.CASCADE, related_name='guests', verbose_name='Размещение')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='guest_records', verbose_name='Пользователь')
    is_primary = models.BooleanField(default=False, verbose_name='Основной гость')
    check_in_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата заселения')
    special_requests = models.TextField(null=True, blank=True, verbose_name='Особые пожелания')

    class Meta:
        verbose_name = 'Список проживающих'
        verbose_name_plural = 'Списки проживающих'

    def __str__(self):
        return self.user.username