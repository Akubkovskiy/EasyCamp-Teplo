from pydantic import BaseModel
from typing import Optional


class AvitoWebhookEvent(BaseModel):
    event_type: str
    event_time: int
    payload: dict
