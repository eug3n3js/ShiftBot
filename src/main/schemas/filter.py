from dataclasses import dataclass, field
from datetime import timedelta
from typing import Optional, List


@dataclass(init=True)
class ListFieldBase:
    id: Optional[int] = None
    value: Optional[str] = None


@dataclass(init=True)
class FilterBase:
    id: Optional[int] = None
    user_id: Optional[int] = None
    is_black_list: Optional[bool] = None
    is_and: Optional[bool] = None
    companies: List[ListFieldBase] = field(default_factory=list)
    locations: List[ListFieldBase] = field(default_factory=list)
    positions: List[ListFieldBase] = field(default_factory=list)
    longer: Optional[timedelta] = None
    shorter: Optional[timedelta] = None

