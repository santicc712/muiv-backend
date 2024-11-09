from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
Base = declarative_base()


class Goods(Base):
    __tablename__ = "goods"

    index = Column(Integer, primary_key=True)
    goods_id = Column(BigInteger)
    title = Column(String)
    description = Column(String)
    grams = Column(String)
    photo_url = Column(String)
    price = Column(BigInteger)
