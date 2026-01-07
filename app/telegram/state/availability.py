import datetime
from dataclasses import dataclass


@dataclass
class AvailabilityState:
    check_in: datetime.date | None = None
    check_out: datetime.date | None = None


# user_id -> state
availability_states: dict[int, AvailabilityState] = {}
