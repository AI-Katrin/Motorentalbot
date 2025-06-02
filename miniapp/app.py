import sys
import os
import math
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI, Request, UploadFile, File, Form, Depends, APIRouter, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from aiogram import Bot
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy.orm import Session
from uuid import uuid4
from config import BOT_TOKEN, EMPLOYEE_CHAT_ID
from schemas import BookingCreate
from models import Booking, Motorcycle
from database import get_db
from routers import bookings
from routers import motos

app = FastAPI()
router = APIRouter()
bot = Bot(token=BOT_TOKEN)

# Шаблоны и статика
templates = Jinja2Templates(directory="miniapp/templates")
admin_templates = Jinja2Templates(directory="web/templates")
app.mount("/static", StaticFiles(directory="miniapp/static"), name="static")

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
    moto_obj = db.query(Motorcycle).filter_by(model=moto).first()
    price = moto_obj.price_per_day if moto_obj else 0
    return templates.TemplateResponse("calendar.html", {
        "request": request,
        "moto": moto,
        "user_id": user_id,
        "phone": phone,
        "price_per_day": price
    })

@router.post("/confirm")
async def confirm_rental(rental: BookingCreate, db: Session = Depends(get_db)):
    moto = db.query(Motorcycle).filter_by(model=rental.moto).first()
    if not moto:
        raise HTTPException(status_code=400, detail="Unknown motorcycle")

    try:
        start_dt = datetime.fromisoformat(rental.start)
        end_dt = datetime.fromisoformat(rental.end)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    if end_dt <= start_dt:
        raise HTTPException(status_code=400, detail="End date must be after start date")

    new_booking = Booking(
        moto=rental.moto,
        user_id=rental.user_id,
        phone=rental.phone,
        start_date=rental.start,
        end_date=rental.end,
        services=rental.services,
        equipment_details=rental.equipment_details,
        delivery_address=rental.delivery_address,
        comments=rental.comments,
        base_price=rental.base_price,
        discounted_price=rental.discounted_price,
        extra_services_price=rental.extra_services_price,
        deposit=rental.deposit,
        total=rental.total,
        status="pending",
        source="telegram_miniapp"
    )
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)

    message = (
        f"Новая заявка на аренду мотоцикла:\n\n"
        f"Мотоцикл: {rental.moto}\n"
        f"Период: {start_dt.strftime('%d.%m.%Y')} – {end_dt.strftime('%d.%m.%Y')}\n"
        f"Телефон: {rental.phone}\n"
        f"Telegram ID: {rental.user_id}\n"
        f"Цена без скидки: {rental.base_price:,} руб.\n"
        f"Со скидкой: {rental.discounted_price:,} руб.\n"
        f"Залог: {rental.deposit:,} руб."
    )

    await bot.send_message(EMPLOYEE_CHAT_ID, message)

    return {"message": "Заявка сохранена", "id": new_booking.id}

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
                       moto: str = "", start: str = "", end: str = "", user_id: str = "", phone: str = "",
                       services: str = "", equipment_details: str = "", delivery_address: str = "", comments: str = "",
                       deposit: str = "", base_price: str = "", price_per_day: str = "",
                       discounted_price: str = "", extra_services_price: str = ""):
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
async def show_admin_calendar(request: Request, db: Session = Depends(get_db)):
    motos = db.query(Motorcycle).all()
    bookings = db.query(Booking).all()
    return admin_templates.TemplateResponse("web_calendar.html", {
        "request": request,
        "motos": motos,
        "bookings": bookings
    })

@app.get("/admin/add-moto", response_class=HTMLResponse)
async def admin_add_moto_page(request: Request):
    return admin_templates.TemplateResponse("add_moto.html", {"request": request})

@app.get("/admin/requests", response_class=HTMLResponse)
async def admin_requests(request: Request, db: Session = Depends(get_db)):
    bookings = db.query(Booking).filter(Booking.status == "pending").all()
    return admin_templates.TemplateResponse("requests.html", {"request": request, "bookings": bookings})

@app.post("/admin/requests/confirm/{booking_id}")
async def confirm_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter_by(id=booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    booking.status = "confirmed"
    db.commit()
    return RedirectResponse("/admin/requests", status_code=303)

@app.post("/admin/requests/reject/{booking_id}")
async def reject_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter_by(id=booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    booking.status = "rejected"
    db.commit()
    return RedirectResponse("/admin/requests", status_code=303)

@app.post("/admin/motorcycles")
async def add_motorcycle(
    request: Request,
    brand: str = Form(...),
    model: str = Form(...),
    description: str = Form(...),
    price_per_day: int = Form(...),
    deposit: int = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    image_dir = "miniapp/static/images"
    os.makedirs(image_dir, exist_ok=True)

    ext = image.filename.split('.')[-1]
    filename = f"{uuid4().hex}.{ext}"
    file_path = os.path.join(image_dir, filename)

    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(image.file, f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при сохранении изображения: {e}")

    image_url = f"{request.base_url}static/images/{filename}"

    moto = Motorcycle(
        brand=brand,
        model=model,
        description=description,
        price_per_day=price_per_day,
        deposit=deposit,
        image_url=image_url
    )
    db.add(moto)
    db.commit()
    db.refresh(moto)

    return JSONResponse(content={
        "id": moto.id,
        "brand": moto.brand,
        "model": moto.model,
        "name": f"{moto.brand} {moto.model}",
        "description": moto.description,
        "price_per_day": moto.price_per_day,
        "deposit": moto.deposit,
        "image_url": moto.image_url
    })

@app.delete("/api/motorcycles/{moto_id}")
async def delete_motorcycle(moto_id: int, db: Session = Depends(get_db)):
    moto = db.query(Motorcycle).filter(Motorcycle.id == moto_id).first()
    if not moto:
        raise HTTPException(status_code=404, detail="Мотоцикл не найден")
    db.delete(moto)
    db.commit()
    return {"message": "Мотоцикл удалён"}

app.include_router(bookings.router)
app.include_router(motos.router)
app.include_router(router, prefix="/app")
