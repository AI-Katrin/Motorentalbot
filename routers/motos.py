import shutil
import os

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Motorcycle
from schemas import MotoOut
from uuid import uuid4

router = APIRouter(prefix="/motos", tags=["motos"])
IMAGES_DIR = "miniapp/static/images"

os.makedirs(IMAGES_DIR, exist_ok=True)


@router.post("/", response_model=MotoOut)
def create_moto(
    brand: str = Form(...),
    model: str = Form(...),
    description: str = Form(...),
    price_per_day: int = Form(...),
    deposit: int = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    ext = image.filename.split(".")[-1]
    filename = f"{uuid4().hex}.{ext}"
    image_url= os.path.join(IMAGES_DIR, filename)

    try:
        with open(image_url, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при сохранении изображения: {e}")

    moto = Motorcycle(
        brand=brand,
        model=model,
        description=description,
        price_per_day=price_per_day,
        deposit=deposit,
        image_url=f"/static/images/{filename}"
    )
    db.add(moto)
    db.commit()
    db.refresh(moto)
    return moto


@router.get("/", response_model=list[MotoOut])
def list_motos(db: Session = Depends(get_db)):
    return db.query(Motorcycle).all()