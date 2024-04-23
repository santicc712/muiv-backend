from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Float, BLOB
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
Base = declarative_base()


class UserWallet(Base):
    __tablename__ = "user_wallet"

    index = Column(Integer, primary_key=True)
    user_id = Column(BigInteger)
    campaign_id = Column(String)
    wallet = Column(String)
