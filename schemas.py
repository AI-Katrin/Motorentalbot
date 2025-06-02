from pydantic import BaseModel
from typing import Optional, List


class MotoCreate(BaseModel):
    brand: str
    model: str
    description: str
    price_per_day: int
    deposit: int
    image_url: Optional[str] = None


class MotoOut(MotoCreate):
    id: int

    model_config = {
        "from_attributes": True
    }


class MotoBrief(BaseModel):
    id: int
    brand: str
    model: str

    model_config = {
        "from_attributes": True
    }


class BookingCreate(BaseModel):
    moto_id: int
    moto: Optional[str] = None
    user_id: Optional[str] = ""
    phone: Optional[str] = ""
    start: str
    end: str
    services: Optional[str] = ""
    equipment_details: Optional[str] = ""
    delivery_address: Optional[str] = ""
    comments: Optional[str] = ""
    base_price: int = 0
    discounted_price: int = 0
    extra_services_price: int = 0
    deposit: int = 0
    total: int = 0



class BookingOut(BaseModel):
    id: int
    moto_id: int
    moto_obj: MotoBrief  # ✅ вложенная модель мотоцикла
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
    source: Optional[str]

    model_config = {
        "from_attributes": True
    }


class BookingUpdate(BaseModel):
    status: str
