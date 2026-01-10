import datetime
from dataclasses import dataclass


@dataclass
class AvailabilityState:
    check_in: datetime.date | None = None
    check_out: datetime.date | None = None
    selected_house_id: int | None = None
    waiting_for_guest_name: bool = False


# user_id -> state
availability_states: dict[int, AvailabilityState] = {}
