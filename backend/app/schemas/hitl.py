from typing import Literal
from pydantic import BaseModel


class HitlResumeRequest(BaseModel):
    thread_id: str
    action: Literal["approve", "edit_flight", "edit_hotel"]
    selected_flight_id: str | None = None
    selected_hotel_id: str | None = None
