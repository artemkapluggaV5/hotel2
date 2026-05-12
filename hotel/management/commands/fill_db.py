import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from faker import Faker
from hotel.models import Category, Room

# Получаем нашу текущую модель пользователя (которую мы указали в settings.py)
User = get_user_model()

class Command(BaseCommand):
    help = 'Заполняет базу данных фейковыми категориями и номерами'

    def handle(self, *args, **kwargs):
        # Используем русскую локализацию
        fake = Faker('ru_RU')

        self.stdout.write('Удаляем старые данные...')
        # Сначала удаляем комнаты, потом категории (из-за связей ForeignKey)
        Room.objects.all().delete()
        Category.objects.all().delete()

        self.stdout.write('Создаем категории...')
        category_names = ['Стандарт', 'Комфорт', 'Полулюкс', 'Люкс', 'Президентский']
        categories = []

        for name in category_names:
            category = Category.objects.create(
                name=name,
                description=fake.text(max_nb_chars=150),
                max_guests=random.randint(1, 4),
                base_price=round(random.uniform(1500, 15000), 2)
            )
            categories.append(category)

        self.stdout.write('Создаем номера...')
        amenities_list = ['Wi-Fi', 'Кондиционер', 'Мини-бар', 'ТВ', 'Сейф', 'Фен', 'Джакузи', 'Балкон']

        for _ in range(25):
            cat = random.choice(categories)
            room_price = cat.base_price + round(random.uniform(0, 1000), 2)

            Room.objects.create(
                room_number=str(fake.unique.random_int(min=100, max=999)),
                category=cat,
                price=room_price,
                amenities=", ".join(random.sample(amenities_list, k=random.randint(2, 5))),
                features=fake.sentence(nb_words=5),
                description=fake.text(max_nb_chars=200),
                rating=round(random.uniform(3.5, 5.0), 1),
                rules="Заезд после 14:00, выезд до 12:00. Без животных.",
                status=random.choice(['available', 'available', 'available', 'occupied', 'maintenance'])
            )

        self.stdout.write('Проверка суперпользователя...')
        if not User.objects.filter(username='admin').exists():
            # Создаем админа напрямую через модель User
            User.objects.create_superuser(
                username='admin',
                email='admin@hotel.com',
                password='admin',
                role='admin',   # Поле из нашей новой модели
                phone='+70000000000'
            )
            self.stdout.write(self.style.SUCCESS('Создан суперпользователь: admin / admin'))

        self.stdout.write(self.style.SUCCESS('✅ База успешно заполнена!'))