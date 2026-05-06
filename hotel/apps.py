from django.apps import AppConfig


class HotelConfig(AppConfig):
    name = 'hotel'
    def ready(self):
        import hotel.signals