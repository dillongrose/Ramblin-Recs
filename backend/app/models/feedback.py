from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Boolean, Integer, DateTime, ForeignKey, BigInteger
from sqlalchemy.sql import func
from ..db import Base

class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True),
                                          ForeignKey("users.id", ondelete="CASCADE"),
                                          index=True)
    event_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True),
                                           ForeignKey("events.id", ondelete="CASCADE"),
                                           index=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    clicked = mapped_column(Boolean, default=False)
    saved = mapped_column(Boolean, default=False)
    rsvp = mapped_column(Boolean, default=False)
    dwell_seconds = mapped_column(Integer, default=0)
