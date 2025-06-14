from sqlalchemy import Column, Integer, String, Enum, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
import enum


class BookingStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    declined = "declined"
    blocked = "blocked"


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    moto_id = Column(Integer, ForeignKey("motos.id"), nullable=False)
    moto_obj = relationship("Motorcycle", backref="bookings")

    moto = Column(String)  # Название модели для отображения, необязательно
    user_id = Column(String)
    phone = Column(String)

    start_date = Column(String)
    end_date = Column(String)

    services = Column(String)
    equipment_details = Column(String)
    delivery_address = Column(String)
    comments = Column(String)

    base_price = Column(Integer)
    discounted_price = Column(Integer)
    extra_services_price = Column(Integer)
    deposit = Column(Integer)
    total = Column(Integer)

    price_per_day = Column(Integer)
    days_count = Column(Integer)

    status = Column(Enum(BookingStatus), default=BookingStatus.pending)
    source = Column(String, default="telegram_app")


class Motorcycle(Base):
    __tablename__ = "motos"

    id = Column(Integer, primary_key=True, index=True)
    brand = Column(String, nullable=False)
    model = Column(String, nullable=False)
    description = Column(String, nullable=True)
    price_per_day = Column(Integer, nullable=False)
    deposit = Column(Integer, nullable=False)
    image_url = Column(String, nullable=True)
