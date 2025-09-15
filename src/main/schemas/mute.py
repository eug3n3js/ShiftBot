from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(init=True)
class MuteBase:
    id: Optional[int] = None
    user_id: Optional[int] = None
    shift_link: Optional[int] = None
    created_at: Optional[datetime] = None
