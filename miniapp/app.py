from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
import math


app = FastAPI()
router = APIRouter()

# Подключаем папку с шаблонами и статикой
templates = Jinja2Templates(directory="miniapp/templates")
app.mount("/static", StaticFiles(directory="miniapp/static"), name="static")

# Данные о мотоциклах
motorcycles = [
    {
        "image": "/static/images/bmw_r1250gs.jpg",
        "name": "BMW R 1250 GS",
        "price": "15 000 руб.",
        "deposit": "50 000 руб.",
        "description": "BMW R 1250 GS — самая популярная модель мотоциклов BMW GS-серии. Будь то город, трасса или бездорожье — на любом покрытии GS даст вам ещё больше свободы и удовольствия от езды.",
        "specs": (
            "Класс мотоцикла: турэндуро\n"
            "Двигатель: 2-цилиндровый оппозитный, 1254 см³\n"
            "Мощность: 100 кВт (136 л.с.) при 7750 об/мин\n"
            "Крутящий момент: 143 Нм при 6250 об/мин\n"
            "Макс. скорость: свыше 200 км/ч\n"
            "Объём бака: 20 л\n"
            "Цвет: белый"
        )
    },
    {
        "image": "/static/images/bmw_r1250rt.jpg",
        "name": "BMW R 1250 RT",
        "price": "18 000 руб.",
        "deposit": "50 000 руб.",
        "description": "BMW R 1250 RT — идеальный мотоцикл для дальних путешествий. Комфорт, мощь и надёжность — всё, что нужно для уверенной езды по трассе.",
        "specs": (
            "Класс мотоцикла: туристический\n"
            "Двигатель: 2-цилиндровый оппозитный, 1254 см³\n"
            "Мощность: 100 кВт (136 л.с.) при 7750 об/мин\n"
            "Крутящий момент: 143 Нм при 6250 об/мин\n"
            "Макс. скорость: 210 км/ч\n"
            "Объём бака: 25 л\n"
            "Цвет: белый"
        )
    },
    {
        "image": "/static/images/bmw_r18.jpg",
        "name": "BMW R 18",
        "price": "18 000 руб.",
        "deposit": "50 000 руб.",
        "description": "BMW R 18 — харизматичный круизёр в стиле Heritage. Классический дизайн с современными технологиями и мощным 1802 см³ двигателем.",
        "specs": (
            "Класс мотоцикла: круизёр\n"
            "Двигатель: 2-цилиндровый оппозитный, 1802 см³\n"
            "Мощность: 67 кВт (91 л.с.) при 4750 об/мин\n"
            "Крутящий момент: 158 Нм при 3000 об/мин\n"
            "Макс. скорость: свыше 180 км/ч\n"
            "Объём бака: 16 л\n"
            "Цвет: чёрный"
        )
    }
]

motorcycle_data = {
    "BMW R 1250 GS": {"price": 15000, "deposit": 50000},
    "BMW R 1250 RT": {"price": 18000, "deposit": 50000},
    "BMW R 18": {"price": 18000, "deposit": 50000},
}

class RentalRequest(BaseModel):
    user_id: str
    phone: str
    motorcycle: str
    start: str
    end: str

def calculate_discount(days: int) -> float:
    if days >= 30:
        return 0.25
    elif days >= 20:
        return 0.20
    elif days >= 11:
        return 0.15
    elif days >= 7:
        return 0.10
    else:
        return 0.0

@router.get("/rent", response_class=HTMLResponse)
async def rent_page(request: Request):
    return templates.TemplateResponse("rent.html", {"request": request, "motorcycles": motorcycles})

@router.post("/rent")
async def process_rent(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    phone = data.get("phone")
    motorcycle = data.get("motorcycle")

    if not user_id or not phone or not motorcycle:
        return JSONResponse(status_code=400, content={"error": "Invalid request"})

    message = (
        f"Новый заказ на аренду мотоцикла\n\n"
        f"Пользователь ID: {user_id}\n"
        f"Телефон: {phone}\n"
        f"Мотоцикл: {motorcycle['name']}\n"
        f"Цена: {motorcycle['price']}\n"
        f"Депозит: {motorcycle['deposit']}"
    )

    await bot.send_message(EMPLOYEE_CHAT_ID, message)
    print(message)
    return JSONResponse(status_code=200, content={"message": "Заказ успешно оформлен"})

@router.get("/calendar", response_class=HTMLResponse)
async def calendar_page(request: Request, moto: str = "", user_id: str = "", phone: str = ""):
    return templates.TemplateResponse("calendar.html", {
        "request": request,
        "moto": moto,
        "user_id": user_id,
        "phone": phone
    })

@router.post("/confirm")
async def confirm_rental(rental: RentalRequest):
    moto_info = motorcycle_data.get(rental.motorcycle)
    if not moto_info:
        return JSONResponse(status_code=400, content={"error": "Unknown motorcycle"})

    try:
        start_dt = datetime.fromisoformat(rental.start)
        end_dt = datetime.fromisoformat(rental.end)
    except ValueError:
        return JSONResponse(status_code=400, content={"error": "Invalid date format"})

    if end_dt <= start_dt:
        return JSONResponse(status_code=400, content={"error": "End date must be after start date"})

    duration = (end_dt - start_dt).total_seconds() / (24 * 3600)
    days = math.ceil(duration)

    discount_rate = calculate_discount(days)
    total_price = days * moto_info["price"] * (1 - discount_rate)

    message = (
        f"Новый заказ на аренду мотоцикла:\n\n"
        f"Пользователь ID: {rental.user_id}\n"
        f"Телефон: {rental.phone}\n"
        f"Мотоцикл: {rental.motorcycle}\n"
        f"Период: {start_dt.strftime('%d.%m.%Y')} — {end_dt.strftime('%d.%m.%Y')}\n"
        f"Дней: {days}\n"
        f"Скидка: {int(discount_rate * 100)}%\n"
        f"Итоговая цена: {int(total_price):,} руб.\n"
        f"Залог: {moto_info['deposit']:,} руб."
    )

    await bot.send_message(EMPLOYEE_CHAT_ID, message)
    print(message)
    return JSONResponse(status_code=200, content={"message": "Заказ успешно оформлен"})

# 👇 ВАЖНО: подключаем маршруты с префиксом /app
app.include_router(router, prefix="/app")