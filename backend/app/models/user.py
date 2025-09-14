import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String, JSON, DateTime
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from ..db import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String, nullable=True)
    interests = mapped_column(JSON, nullable=True)
    embed = mapped_column(Vector(384), nullable=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
