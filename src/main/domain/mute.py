from sqlalchemy import Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from .base import Base


class Mute(Base):
    __tablename__ = "mutes"
    
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    shift_link: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship to user
    user = relationship("User", back_populates="mutes")
    
    # Unique constraint to prevent duplicate mutes
    __table_args__ = (
        UniqueConstraint('user_id', 'shift_link', name='unique_user_shift_mute'),
    )
