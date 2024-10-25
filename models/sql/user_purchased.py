from sqlalchemy import Column, Integer, String, DateTime, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
Base = declarative_base()


class UserPurchased(Base):
    __tablename__ = "user_purchased"

    index = Column(Integer, primary_key=True)
    id = Column(BigInteger)
    card_id = Column(BigInteger)
