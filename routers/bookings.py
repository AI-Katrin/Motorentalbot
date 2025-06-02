from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from database import get_db
from models import Booking, Motorcycle
from schemas import BookingOut, BookingUpdate, BookingCreate

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.get("/", response_model=list[BookingOut])
def get_all_bookings(db: Session = Depends(get_db)):
    return db.query(Booking).all()


@router.patch("/{booking_id}")
def update_booking(booking_id: int, update: BookingUpdate, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    booking.status = update.status
    db.commit()
    return {"message": f"Booking {booking_id} updated to {update.status}"}


@router.post("/confirm")
def create_booking(data: BookingCreate, db: Session = Depends(get_db)):
    # Поиск мотоцикла по полному имени
    moto = db.query(Motorcycle).filter(
        func.concat(Motorcycle.brand, " ", Motorcycle.model) == data.moto
    ).first()

    if not moto:
        raise HTTPException(status_code=404, detail="Мотоцикл не найден")

    try:
        start_date = datetime.fromisoformat(data.start)
        end_date = datetime.fromisoformat(data.end)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат даты")

    booking = Booking(
        moto_id=moto.id,
        user_id=data.user_id,
        phone=data.phone,
        start_date=start_date,
        end_date=end_date,
        services=data.services,
        equipment_details=data.equipment_details,
        delivery_address=data.delivery_address,
        comments=data.comments,
        base_price=data.base_price,
        discounted_price=data.discounted_price,
        extra_services_price=data.extra_services_price,
        deposit=data.deposit,
        total=data.total,
        source="web_admin",
        status="pending"
    )

    db.add(booking)
    db.commit()
    db.refresh(booking)
    return {"message": "Бронирование создано", "booking_id": booking.id}
