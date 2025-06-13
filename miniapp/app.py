import os
import shutil
import logging
import traceback

from uuid import uuid4
from datetime import datetime
from fastapi import FastAPI, Request, UploadFile, File, Form, Depends, APIRouter, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY
from aiogram import Bot
from config import BOT_TOKEN, EMPLOYEE_CHAT_ID
from schemas import BookingCreate
from models import Booking, Motorcycle
from database import get_db
from routers import bookings, motos
from miniapp.amocrm import send_lead_to_amocrm

logger = logging.getLogger("uvicorn.error")

app = FastAPI()
router = APIRouter()
bot = Bot(token=BOT_TOKEN)

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

@router.post("/confirm")
async def confirm_rental(rental: BookingCreate, db: Session = Depends(get_db)):
    try:
        logger.info("Получен запрос: %s", rental.dict())

        moto = db.query(Motorcycle).filter_by(id=rental.moto_id).first()
        if not moto:
            logger.warning("Неизвестный mотоцикл с ID: %s", rental.moto_id)
            raise HTTPException(status_code=400, detail="Unknown motorcycle ID")

        try:
            start_dt = datetime.fromisoformat(rental.start.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(rental.end.replace("Z", "+00:00"))
        except ValueError as e:
            logger.error("Ошибка формата даты: %s", e)
            raise HTTPException(status_code=400, detail="Invalid date format")

        if end_dt <= start_dt:
            logger.warning("Дата окончания раньше или равна дате начала")
            raise HTTPException(status_code=400, detail="End date must be after start date")

        days_count = (end_dt - start_dt).days + 1
        price_per_day = moto.price_per_day

        new_booking = Booking(
            moto_id=rental.moto_id,
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
            price_per_day=rental.price_per_day,
            days_count=rental.days_count,
            status="pending",
            source="telegram_miniapp"
        )
        db.add(new_booking)
        db.commit()
        db.refresh(new_booking)

        try:
            await send_lead_to_amocrm({
                "id": new_booking.id,
                "moto": new_booking.moto,
                "start": new_booking.start_date,
                "end": new_booking.end_date,
                "price_per_day": new_booking.price_per_day,
                "days_count": new_booking.days_count,
                "phone": new_booking.phone,
                "user_id": new_booking.user_id,
                "base_price": new_booking.base_price,
                "discounted_price": new_booking.discounted_price,
                "extra_services_price": new_booking.extra_services_price,
                "deposit": new_booking.deposit,
                "total": new_booking.total,
                "services": new_booking.services,
                "equipment_details": new_booking.equipment_details,
                "delivery_address": new_booking.delivery_address,
                "comments": new_booking.comments
            })
            logger.info("Заявка отправлена в amoCRM")
        except Exception as amo_err:
            logger.error(f"Ошибка при отправке в amoCRM: {amo_err}")


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
        logger.info("Заявка успешно создана: %s", new_booking.id)

        return {"message": "Заявка сохранена", "id": new_booking.id}

    except Exception as e:
        logger.error("Ошибка в confirm_rental: %s", str(e))
        traceback.print_exc()
        raise HTTPException(status_code=400, detail="Internal error")

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

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"[VALIDATION ERROR] URL: {request.url}")
    logger.error(f"[VALIDATION ERROR] Body: {await request.body()}")
    logger.error(f"[VALIDATION ERROR] Details: {exc.errors()}")
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()}
    )