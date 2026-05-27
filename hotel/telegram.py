import requests
from django.conf import settings


def send_telegram_message(chat_id, text):
    if not chat_id:
        print("Телеграм: У пользователя нет ID.")
        return

    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
    if not token:
        print("Телеграм ОШИБКА: Не указан TELEGRAM_BOT_TOKEN в settings.py!")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }

    try:
        response = requests.post(url, data=data)
        print(f"Ответ от Telegram API: {response.json()}")
    except Exception as e:
        print(f"Системная ошибка при отправке в Telegram: {e}")