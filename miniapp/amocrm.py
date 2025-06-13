import os
import httpx
import logging
from datetime import datetime

logger = logging.getLogger("uvicorn.error")

AMO_SUBDOMAIN = os.getenv("AMOCRM_SUBDOMAIN")
ACCESS_TOKEN = os.getenv("AMOCRM_ACCESS_TOKEN")
PIPELINE_ID = os.getenv("AMO_PIPELINE_ID")
STATUS_ID = os.getenv("AMO_STATUS_ID")
RESPONSIBLE_USER_ID = os.getenv("AMO_RESPONSIBLE_USER_ID")

FIELD_IDS = {
    "Мотоцикл": 1861285,
    "Дата начала": 1861287,
    "Дата окончания": 1861289,
    "Цена за сутки": 1861291,
    "Дней": 1861293,
    "Базовая цена": 1861297,
    "Цена со скидкой": 1861299,
    "Доп. услуги": 1861301,
    "Стоимость доп. услуг": 1861303,
    "Залог": 1861305,
    "Итого": 1861307,
    "Экипировка": 1861309,
    "Адрес доставки": 1861311,
    "Комментарий": 1861313,
}

async def send_lead_to_amocrm(data: dict):
    url = f"https://{AMO_SUBDOMAIN}.amocrm.ru/api/v4/leads/complex"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    start_date = datetime.fromisoformat(data["start"]).strftime("%d.%m.%Y")
    end_date = datetime.fromisoformat(data["end"]).strftime("%d.%m.%Y")

    custom_fields_values = [
        {"field_id": FIELD_IDS["Мотоцикл"], "values": [{"value": data["moto"]}]},
        {"field_id": FIELD_IDS["Дата начала"], "values": [{"value": start_date}]},
        {"field_id": FIELD_IDS["Дата окончания"], "values": [{"value": end_date}]},
        {"field_id": FIELD_IDS["Цена за сутки"], "values": [{"value": data["price_per_day"]}]},
        {"field_id": FIELD_IDS["Дней"], "values": [{"value": data["days_count"]}]},
        {"field_id": FIELD_IDS["Базовая цена"], "values": [{"value": data["base_price"]}]},
        {"field_id": FIELD_IDS["Цена со скидкой"], "values": [{"value": data["discounted_price"]}]},
        {"field_id": FIELD_IDS["Доп. услуги"], "values": [{"value": data.get("services", "")}]},
        {"field_id": FIELD_IDS["Стоимость доп. услуг"], "values": [{"value": data["extra_services_price"]}]},
        {"field_id": FIELD_IDS["Залог"], "values": [{"value": data["deposit"]}]},
        {"field_id": FIELD_IDS["Итого"], "values": [{"value": data["total"]}]},
        {"field_id": FIELD_IDS["Экипировка"], "values": [{"value": data.get("equipment_details", "")}]},
        {"field_id": FIELD_IDS["Адрес доставки"], "values": [{"value": data.get("delivery_address", "")}]},
        {"field_id": FIELD_IDS["Комментарий"], "values": [{"value": data.get("comments", "")}]},
    ]

    lead = {
        "name": f"Заявка на аренду: {data['moto']}",
        "pipeline_id": int(PIPELINE_ID),
        "status_id": int(STATUS_ID),
        "responsible_user_id": int(RESPONSIBLE_USER_ID),
        "price": int(data["total"]),
        "custom_fields_values": custom_fields_values
    }

    contact = {
        "first_name": "Клиент",
        "custom_fields_values": [
            {
                "field_code": "PHONE",
                "values": [{"value": data.get("phone", "")}]
            }
        ],
        "_embedded": {
            "leads": [{}]
        }
    }

    payload = [
        {
            **lead,
            "_embedded": {
                "contacts": [contact]
            }
        }
    ]

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        logger.error(f"[amoCRM] Payload: {payload}")
        logger.error(f"[amoCRM] Response: {response.status_code} — {response.text}")
        response.raise_for_status()
        return response.json()