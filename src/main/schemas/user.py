from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(init=True)
class UserBase:
    id: Optional[int] = None
    tg_id: Optional[int] = None
    is_admin: Optional[bool] = None
    access_ends: Optional[datetime] = None
    created_at: Optional[datetime] = None

