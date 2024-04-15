from sqlalchemy import Column, Integer, String, DateTime, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
Base = declarative_base()


class Admin(Base):
    __tablename__ = "admin"

    index = Column(Integer, primary_key=True)
    id = Column(BigInteger)



