from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

app = FastAPI()

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

@app.get("/rent", response_class=HTMLResponse)
async def rent_page(request: Request):
    return templates.TemplateResponse("rent.html", {"request": request, "motorcycles": motorcycles})

#Обработчик заказа на аренду
@app.post("/api/rent")
async def process_rent(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    phone = data.get("phone")
    motorcycle = data.get("motorcycle")

    if not user_id or not phone or not motorcycle:
        return JSONResponse(status_code=400, content={"error": "Invalid request"})

    # Формируем сообщение о заказе
    message = (
        f"Новый заказ на аренду мотоцикла\n\n"
        f"Пользователь ID: {user_id}\n"
        f"Телефон: {phone}\n"
        f"Мотоцикл: {motorcycle['name']}\n"
        f"Цена: {motorcycle['price']}\n"
        f"Депозит: {motorcycle['deposit']}"
    )
    # Отправляем уведомление в Telegram менеджеру (EMPLOYEE_CHAT_ID)
    await bot.send_message(EMPLOYEE_CHAT_ID, message)
    return JSONResponse(status_code=200, content={"message": "Заказ успешно оформлен"})

#Убирает предупреждение
@app.get("/rent", response_class=HTMLResponse)
async def rent_page(request: Request):
    headers = {"ngrok-skip-browser-warning": "true"}  # Добавляем заголовок
    return templates.TemplateResponse("rent.html", {"request": request, "motorcycles": motorcycles}, headers=headers)
