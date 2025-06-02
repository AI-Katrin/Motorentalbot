import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI, Request, UploadFile, File, Form, Depends, APIRouter, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from aiogram import Bot
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy.orm import Session
import math
import shutil
from config import BOT_TOKEN, EMPLOYEE_CHAT_ID
from schemas import BookingCreate
from models import Booking, Motorcycle
from database import get_db
from routers import bookings, motos

app = FastAPI()
router = APIRouter()
bot = Bot(token=BOT_TOKEN)

# Шаблоны и статика
templates = Jinja2Templates(directory="miniapp/templates")
admin_templates = Jinja2Templates(directory="web/templates")
app.mount("/static", StaticFiles(directory="miniapp/static"), name="static")

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
    return 0.0

@router.get("/rent", response_class=HTMLResponse)
async def rent_page(request: Request, db: Session = Depends(get_db)):
    motos = db.query(Motorcycle).all()
    return templates.TemplateResponse("rent.html", {"request": request, "motorcycles": motos})

@router.get("/calendar", response_class=HTMLResponse)
async def calendar_page(request: Request, moto: str = "", user_id: str = "", phone: str = "", db: Session = Depends(get_db)):
    moto_obj = db.query(Motorcycle).filter_by(name=moto).first()
    price = moto_obj.price_per_day if moto_obj else 0
    return templates.TemplateResponse("calendar.html", {
        "request": request,
        "moto": moto,
        "user_id": user_id,
        "phone": phone,
        "price_per_day": price
    })

@router.post("/confirm")
async def confirm_rental(rental: RentalRequest, db: Session = Depends(get_db)):
    moto = db.query(Motorcycle).filter_by(name=rental.motorcycle).first()
    if not moto:
        return JSONResponse(status_code=400, content={"error": "Unknown motorcycle"})

    try:
        start_dt = datetime.fromisoformat(rental.start)
        end_dt = datetime.fromisoformat(rental.end)
    except ValueError:
        return JSONResponse(status_code=400, content={"error": "Invalid date format"})

    if end_dt <= start_dt:
        return JSONResponse(status_code=400, content={"error": "End date must be after start date"})

    days = math.ceil((end_dt - start_dt).total_seconds() / (24 * 3600))
    discount_rate = calculate_discount(days)
    base_price = days * moto.price_per_day
    discounted_price = base_price * (1 - discount_rate)

    message = (
        f"Новая заявка на аренду мотоцикла:\n\n"
        f"Мотоцикл: {rental.motorcycle}\n"
        f"Начало: {start_dt.strftime('%d.%m.%Y')}\n"
        f"Окончание: {end_dt.strftime('%d.%m.%Y')}\n"
        f"Телефон: {rental.phone}\n"
        f"Telegram ID: {rental.user_id}\n"
        f"Без скидки: {int(base_price):,} руб.\n"
        f"Со скидкой: {int(discounted_price):,} руб.\n"
        f"Залог: {moto.deposit:,} руб."
    )

    await bot.send_message(EMPLOYEE_CHAT_ID, message)
    print(message)
    return JSONResponse(status_code=200, content={"message": "Заказ успешно оформлен"})

@router.get("/services", response_class=HTMLResponse)
async def services_page(request: Request, moto: str = "", start: str = "", end: str = "", user_id: str = "", phone: str = ""):
    return templates.TemplateResponse("services.html", {
        "request": request,
        "moto": moto,
        "start": start,
        "end": end,
        "user_id": user_id,
        "phone": phone
    })

@router.get("/summary", response_class=HTMLResponse)
async def summary_page(request: Request,
                       moto: str = "",
                       start: str = "",
                       end: str = "",
                       user_id: str = "",
                       phone: str = "",
                       services: str = "",
                       equipment_details: str = "",
                       delivery_address: str = "",
                       comments: str = "",
                       deposit: str = "",
                       base_price: str = "",
                       price_per_day: str = "",
                       discounted_price: str = "",
                       extra_services_price: str = ""):
    return templates.TemplateResponse("summary.html", {
        "request": request,
        "moto": moto,
        "start": start,
        "end": end,
        "user_id": user_id,
        "phone": phone,
        "services": services,
        "equipment_details": equipment_details,
        "delivery_address": delivery_address,
        "comments": comments,
        "deposit": deposit,
        "base_price": base_price,
        "price_per_day": price_per_day,
        "discounted_price": discounted_price,
        "extra_services_price": extra_services_price
    })

@app.get("/admin/calendar", response_class=HTMLResponse)
async def show_admin_calendar(request: Request):
    return admin_templates.TemplateResponse("web_calendar.html", {"request": request})

@app.get("/admin/add-moto", response_class=HTMLResponse)
async def admin_add_moto_page(request: Request):
    return admin_templates.TemplateResponse("add_moto.html", {"request": request})

@app.get("/admin/requests", response_class=HTMLResponse)
async def admin_requests(request: Request):
    return admin_templates.TemplateResponse("requests.html", {"request": request})

@app.post("/admin/motorcycles")
async def add_motorcycle(
    brand: str = Form(...),
    model: str = Form(...),
    description: str = Form(...),
    price_per_day: int = Form(...),
    deposit: int = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    file_path = f"miniapp/static/uploads/{image.filename}"
    with open(file_path, "wb") as f:
        shutil.copyfileobj(image.file, f)

    moto = Motorcycle(
        brand=brand,
        model=model,
        name=f"{brand} {model}",
        description=description,
        price_per_day=price_per_day,
        deposit=deposit,
        image_url=f"/static/uploads/{image.filename}"
    )
    db.add(moto)
    db.commit()
    db.refresh(moto)
    return {"message": "Мотоцикл добавлен", "id": moto.id}

@app.delete("/api/motorcycles/{moto_id}")
async def delete_motorcycle(moto_id: int, db: Session = Depends(get_db)):
    moto = db.query(Motorcycle).filter(Motorcycle.id == moto_id).first()
    if not moto:
        raise HTTPException(status_code=404, detail="Мотоцикл не найден")
    db.delete(moto)
    db.commit()
    return {"message": "Мотоцикл удалён"}

@router.post("/amo-lead")
async def create_amo_lead(data: BookingCreate, db: Session = Depends(get_db)):
    booking = Booking(
        moto=data.moto,
        user_id=data.user_id,
        phone=data.phone,
        start_date=data.start,
        end_date=data.end,
        services=data.services,
        equipment_details=data.equipment_details,
        delivery_address=data.delivery_address,
        comments=data.comments,
        base_price=data.base_price,
        discounted_price=data.discounted_price,
        extra_services_price=data.extra_services_price,
        deposit=data.deposit,
        total=data.total,
        status="pending",
        source="telegram_miniapp"
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return {"message": "Заявка сохранена", "id": booking.id}


app.include_router(bookings.router)
app.include_router(motos.router)
app.include_router(router, prefix="/app")
