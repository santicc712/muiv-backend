from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Questions(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role = Column(String, nullable=False)       # student | entrant
    fio = Column(String, nullable=False)        # ФИО
    topic = Column(String, nullable=False)      # Тема обращения
    group = Column(String, nullable=True)       # Группа (только для студентов)
    phone = Column(String, nullable=False)      # Телефон
    message = Column(Text, nullable=False)      # Текст обращения
    created_at = Column(DateTime, default=datetime.utcnow)  # Дата/время создания
