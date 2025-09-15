from sqlalchemy import Boolean, String, ForeignKey, Interval
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import timedelta
from .base import Base


class Filter(Base):
    __tablename__ = "filters"
    
    is_black_list: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_and: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    longer: Mapped[timedelta] = mapped_column(Interval, nullable=True)
    shorter: Mapped[timedelta] = mapped_column(Interval, nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="filters")
    companies = relationship("FilterCompany", back_populates="filter")
    locations = relationship("FilterLocation", back_populates="filter")
    positions = relationship("FilterPosition", back_populates="filter")


class FilterCompany(Base):
    __tablename__ = "filter_companies"
    
    filter_id: Mapped[int] = mapped_column(ForeignKey("filters.id"), nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    filter = relationship("Filter", back_populates="companies")


class FilterLocation(Base):
    __tablename__ = "filter_locations"
    
    filter_id: Mapped[int] = mapped_column(ForeignKey("filters.id"), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    filter = relationship("Filter", back_populates="locations")


class FilterPosition(Base):
    __tablename__ = "filter_positions"

    filter_id: Mapped[int] = mapped_column(ForeignKey("filters.id"), nullable=False)
    position: Mapped[str] = mapped_column(String(255), nullable=False)
    filter = relationship("Filter", back_populates="positions")
