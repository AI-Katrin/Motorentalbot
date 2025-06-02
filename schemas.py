from pydantic import BaseModel
from typing import Optional

class MotoCreate(BaseModel):
    brand: str
    model: str
    description: str
    price_per_day: int
    deposit: int
    image_path: Optional[str] = None

class MotoOut(MotoCreate):
    id: int

    class Config:
        orm_mode = True

class BookingCreate(BaseModel):
    moto: str
    user_id: Optional[str]
    phone: Optional[str]
    start: str
    end: str
    services: Optional[str]
    equipment_details: Optional[str]
    delivery_address: Optional[str]
    comments: Optional[str]
    base_price: Optional[int]
    discounted_price: Optional[int]
    extra_services_price: Optional[int]
    deposit: Optional[int]
    total: Optional[int]


class BookingOut(BaseModel):
    id: int
    moto: str
    user_id: Optional[str]
    phone: Optional[str]
    start_date: str
    end_date: str
    services: Optional[str]
    equipment_details: Optional[str]
    delivery_address: Optional[str]
    comments: Optional[str]
    base_price: Optional[int]
    discounted_price: Optional[int]
    extra_services_price: Optional[int]
    deposit: Optional[int]
    total: Optional[int]
    status: str

    class Config:
        orm_mode = True

class BookingUpdate(BaseModel):
    status: str
