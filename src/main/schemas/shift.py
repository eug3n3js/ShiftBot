from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass(init=True)
class ShiftBase:
    name: Optional[str] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    location: Optional[str] = None
    company: Optional[str] = None
    occupied: Optional[int] = None
    max_occupy: Optional[int] = None
    link: int = None
    position: str = None
    is_bind: bool = False
    connected_shifts: list['ShiftBase'] = field(default_factory=list)

    def __hash__(self) -> int:
        connected_shifts_hash = list()
        for c_shift in self.connected_shifts:
            connected_shifts_hash.append(c_shift.__hash__())
        return hash(
            (self.name, self.start, self.end, self.location, self.company, self.max_occupy, self.link, *connected_shifts_hash)
        )
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, ShiftBase):
            return False
        return (self.name == other.name and 
                self.start == other.start and 
                self.end == other.end and 
                self.location == other.location and 
                self.company == other.company and
                self.max_occupy == other.max_occupy and 
                self.link == other.link and
                set(self.connected_shifts) - set(other.connected_shifts)) == set()
    
