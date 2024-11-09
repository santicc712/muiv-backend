from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
Base = declarative_base()


class Additions(Base):
    __tablename__ = "additions"

    index = Column(Integer, primary_key=True)
    goods_id = Column(BigInteger)
    additions_id = Column(BigInteger)
    title = Column(String)
    price = Column(BigInteger)
