import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from faker import Faker
from hotel.models import Category, Room


class Command(BaseCommand):
    help = 'Заполняет базу данных фейковыми категориями и номерами'

    def handle(self, *args, **kwargs):
        # Используем русскую локализацию для реалистичных данных
        fake = Faker('ru_RU')

        self.stdout.write('Удаляем старые данные (чтобы не было дублей)...')
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

        for _ in range(25):  # Создаем 25 номеров
            cat = random.choice(categories)
            # Берем базовую цену категории и добавляем случайную наценку
            room_price = cat.base_price + round(random.uniform(0, 1000), 2)

            Room.objects.create(
                room_number=str(fake.unique.random_int(min=100, max=999)),  # Уникальный номер
                category=cat,
                price=room_price,
                amenities=", ".join(random.sample(amenities_list, k=random.randint(2, 5))),
                features=fake.sentence(nb_words=5),
                description=fake.text(max_nb_chars=200),
                rating=round(random.uniform(3.5, 5.0), 1),
                rules="Заезд после 14:00, выезд до 12:00. Без животных.",
                status=random.choice(['available', 'available', 'available', 'occupied', 'maintenance'])
            )

        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser('admin', 'admin@mail.ru', 'admin')
            admin.profile.role = 'admin'
            admin.profile.save()
            self.stdout.write('Создан суперпользователь: логин "admin", пароль "admin"')

        self.stdout.write(self.style.SUCCESS('✅ База успешно заполнена! Создано 5 категорий и 25 номеров.'))