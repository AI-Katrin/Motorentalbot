import os
import httpx
from datetime import datetime

AMO_SUBDOMAIN = os.getenv("AMOCRM_SUBDOMAIN")
ACCESS_TOKEN = os.getenv("AMOCRM_ACCESS_TOKEN")
PIPELINE_ID = os.getenv("AMO_PIPELINE_ID")
STATUS_ID = os.getenv("AMO_STATUS_ID")
RESPONSIBLE_USER_ID = os.getenv("AMO_RESPONSIBLE_USER_ID")

async def send_lead_to_amocrm(data: dict):
    url = f"https://{AMO_SUBDOMAIN}.amocrm.ru/api/v4/leads/complex"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    start_date = datetime.fromisoformat(data["start"]).strftime("%d.%m.%Y")
    end_date = datetime.fromisoformat(data["end"]).strftime("%d.%m.%Y")

    note = (
        f"ID: {data.get('id', '–')}\n"
        f"Мотоцикл: {data['moto']}\n"
        f"Дата начала: {start_date}\n"
        f"Дата окончания: {end_date}\n"
        f"Цена за сутки: {data['price_per_day']} руб.\n"
        f"Дней: {data['days_count']}\n"
        f"Телефон: {data.get('phone', '–')}\n"
        f"Telegram ID: {data.get('user_id', '–')}\n"
        f"Базовая цена: {data['base_price']} руб.\n"
        f"Цена со скидкой: {data['discounted_price']} руб.\n"
        f"Доп. услуги: {data.get('services', '–')}\n"
        f"Стоимость доп. услуг: {data['extra_services_price']} руб.\n"
        f"Залог: {data['deposit']} руб.\n"
        f"Итого: {data['total']} руб.\n"
        f"Экипировка: {data.get('equipment_details', '–')}\n"
        f"Адрес доставки: {data.get('delivery_address', '–')}\n"
        f"Комментарий: {data.get('comments', '–')}"
    )

    payload = [{
        "name": f"Заявка на аренду: {data['moto']}",
        "pipeline_id": int(PIPELINE_ID),
        "status_id": int(STATUS_ID),
        "responsible_user_id": int(RESPONSIBLE_USER_ID),
        "price": int(data["total"]),
        "_embedded": {
            "notes": [{
                "note_type": "common",
                "params": {"text": note}
            }]
        }
    }]

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()