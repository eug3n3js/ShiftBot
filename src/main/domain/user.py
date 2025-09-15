from datetime import datetime

from sqlalchemy import Boolean, DateTime, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class User(Base):
    __tablename__ = "users"
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    filters: Mapped["Filter"] = relationship(back_populates="user")
    mutes: Mapped["Mute"] = relationship(back_populates="user")
    access_ends: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow())
    