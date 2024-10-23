from sqlalchemy import Column, Integer, String, DateTime, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
Base = declarative_base()


class User(Base):
    __tablename__ = "user"

    index = Column(Integer, primary_key=True)
    id = Column(BigInteger)
    username = Column(String, default=None)
    count_referrals = Column(BigInteger)
    money = Column(BigInteger)
    profit = Column(BigInteger)
    profit_start = Column(String)
    lvl = Column(Integer)
    channel_one = Column(String)
    channel_two = Column(String)
    channel_inst = Column(String)
    referral_link = Column(String)
