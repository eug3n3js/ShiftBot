from datetime import datetime, timedelta
import re

from ..schemas.shift import ShiftBase


class ShiftConverter:

    @staticmethod
    def parse_shift_data(shift_data: list[str]) -> ShiftBase | None:
        try:
            if len(shift_data) < 7:
                raise ValueError(f"Недостаточно данных для создания смены: {shift_data}")
            name = shift_data[0].strip()
            date_str = shift_data[1].strip()
            time_range_str = shift_data[2].strip()
            location = shift_data[3].strip()
            position = shift_data[4].strip()
            occupancy_str = shift_data[5].strip()
            start_datetime, end_datetime = ShiftConverter._parse_datetime(date_str, time_range_str)

            occupied, max_occupy = ShiftConverter._parse_occupancy(occupancy_str)

            return ShiftBase(
                name=name,
                start=start_datetime,
                end=end_datetime,
                location=location,
                position=position,
                occupied=occupied,
                max_occupy=max_occupy
            )
        except Exception as e:
            return None

    @staticmethod
    def parse_shift_link(link: str) -> int | None:
        link_parts = link.split("/")
        try:
            return int(link_parts[-1])
        except:
            return None


    @staticmethod
    def _parse_datetime(date_str: str, time_range_str: str) -> tuple[datetime, datetime]:
        date_match = re.search(r'(\d+)\.\s*(\d+)\.\s*(\d{4})', date_str)
        if not date_match:
            raise ValueError(f"Неверный формат даты: {date_str}")
        
        day = int(date_match.group(1))
        month = int(date_match.group(2))
        year = int(date_match.group(3))
        
        time_match = re.search(r'(\d{1,2}):(\d{2})\s*-\s*(\d{1,2})\.\s*(\d+)\.\s*(\d{1,2}):(\d{2})', time_range_str)
        if time_match:
            start_hour = int(time_match.group(1))
            start_minute = int(time_match.group(2))
            end_day = int(time_match.group(3))
            end_month = int(time_match.group(4))
            end_hour = int(time_match.group(5))
            end_minute = int(time_match.group(6))
            
            start_datetime = datetime(year, month, day, start_hour, start_minute)
            end_datetime = datetime(year, end_month, end_day, end_hour, end_minute)
        else:
            time_match = re.search(r'(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})', time_range_str)
            if not time_match:
                raise ValueError(f"Неверный формат времени: {time_range_str}")
            
            start_hour = int(time_match.group(1))
            start_minute = int(time_match.group(2))
            end_hour = int(time_match.group(3))
            end_minute = int(time_match.group(4))
            
            start_datetime = datetime(year, month, day, start_hour, start_minute)
            end_datetime = datetime(year, month, day, end_hour, end_minute)
            
            if end_datetime < start_datetime:
                end_datetime += timedelta(days=1)
        
        return start_datetime, end_datetime
    
    @staticmethod
    def _parse_occupancy(occupancy_str: str) -> tuple[int, int]:
        occupancy_match = re.search(r'(\d+)/(\d+)', occupancy_str)
        if not occupancy_match:
            raise ValueError(f"Неверный формат занятости: {occupancy_str}")
        
        occupied = int(occupancy_match.group(1))
        max_occupy = int(occupancy_match.group(2))
        
        return occupied, max_occupy

    @staticmethod
    def validate_shift_data(shift_data: list[str]) -> bool:
        try:
            if len(shift_data) < 6:
                return False
            if not shift_data[0].strip():
                return False
            if not shift_data[1].strip():
                return False
            if not shift_data[2].strip():
                return False
            if not shift_data[3].strip():
                return False
            if not shift_data[4].strip():
                return False
            if not shift_data[5].strip():
                return False
            date_str = shift_data[1].strip()
            if not re.search(r'\d+\.\s*\d+\.\s*\d{4}', date_str):
                return False
            time_str = shift_data[2].strip()
            if not re.search(r'\d{1,2}:\d{2}\s*-\s*\d{1,2}', time_str):
                return False
            occupancy_str = shift_data[5].strip()
            if not re.search(r'\d+/\d+', occupancy_str):
                return False
            return True
        except:
            return False
