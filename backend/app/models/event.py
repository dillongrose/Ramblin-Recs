import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy import String, Text, DateTime, Integer, Float
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from ..db import Base

class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_time = mapped_column(DateTime(timezone=True), nullable=False)
    end_time = mapped_column(DateTime(timezone=True), nullable=True)
    timezone = mapped_column(String, nullable=True)
    location = mapped_column(String, nullable=True)
    host = mapped_column(String, nullable=True)
    price_cents = mapped_column(Integer, nullable=True)
    url = mapped_column(String, nullable=True)

    # ✅ Properly typed ARRAY column
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)

    raw_s3_uri = mapped_column(String, nullable=True)

    # ✅ pgvector column
    embed = mapped_column(Vector(384), nullable=True)

    popularity = mapped_column(Float, server_default="0")
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
