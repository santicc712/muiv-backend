from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Float, BLOB
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
Base = declarative_base()


class DoneTask(Base):
    __tablename__ = "done_task"

    index = Column(Integer, primary_key=True)
    group_id = Column(Integer)
    task_id = Column(Integer)
    user_id = Column(BigInteger)
    campaign_id = Column(String)
