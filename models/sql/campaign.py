from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Float, BLOB, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
Base = declarative_base()


class Campaign(Base):
    __tablename__ = "campaign"

    index = Column(Integer, primary_key=True)
    id = Column(String)
    title = Column(String)
    desc = Column(String)
    one_by_access = Column(Boolean)
    reward_amount = Column(Float)
    reward_currency = Column(String)
    finish_date = Column(String)
    finish_time = Column(String)
    created_at = Column(DateTime, default=datetime.now())
