import typing
from pydantic import BaseModel


class EventBaseModel(BaseModel):
    desc: str = None
    topic: str = None
    price: int = 0

