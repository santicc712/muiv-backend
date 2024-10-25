from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
Base = declarative_base()


class Cards(Base):
    __tablename__ = "cards"

    index = Column(Integer, primary_key=True)
    card_id = Column(BigInteger)
    category = Column(String)
    photo_url = Column(String)
    title = Column(String)
    profit = Column(Float)
    price = Column(BigInteger)
