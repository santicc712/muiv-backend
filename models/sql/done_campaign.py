from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Float, BLOB
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
Base = declarative_base()


class DoneCampaign(Base):
    __tablename__ = "done_campaign"

    index = Column(Integer, primary_key=True)
    user_id = Column(BigInteger)
    username = Column(String)
    campaign_id = Column(String)
    created_at = Column(DateTime)
