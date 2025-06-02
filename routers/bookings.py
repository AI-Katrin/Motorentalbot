from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Booking
from schemas import BookingOut, BookingUpdate

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
