from sqlalchemy import BigInteger, String, Text, ForeignKey, DateTime, Index, func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from datetime import datetime

from app.db.base import Base


class Attachment(Base):
    __tablename__ = "attachment"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    key: Mapped[str] = mapped_column(String(255), unique=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chat.id", ondelete="CASCADE"), index=True)
    uploader_id: Mapped[int | None] = mapped_column(ForeignKey("user.id", ondelete="SET NULL"))
    message_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("message.id", ondelete="CASCADE"), index=True
    ) 
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(128))
    size: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
