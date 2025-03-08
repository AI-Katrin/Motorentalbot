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
    {"image": "/static/images/bmw_r1250gs.jpg", "name": "BMW R 1250 GS", "price": "15 000 руб.", "deposit": "50 000 руб."},
    {"image": "/static/images/bmw_r1250rt.jpg", "name": "BMW R 1250 RT", "price": "18 000 руб.", "deposit": "50 000 руб."},
    {"image": "/static/images/bmw_r18.jpg", "name": "BMW R 18", "price": "18 000 руб.", "deposit": "50 000 руб."}
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
