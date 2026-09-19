from datetime import datetime
from pydantic import BaseModel


class ChatHistoryOut(BaseModel):
    id: int
    report_id: int
    question: str
    answer: str
    timestamp: datetime

    class Config:
        from_attributes = True