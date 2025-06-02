from database import Base, engine  # импортируй то, что ты определила в database.py
from models import Motorcycle  # важно: импортируй все модели, иначе они не создадутся

#Base.metadata.create_all(bind=engine)

print("Таблицы успешно созданы.")