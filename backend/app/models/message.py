from typing import TYPE_CHECKING

from sqlalchemy import Text, ForeignKey, func, Index, BigInteger, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from datetime import datetime

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.attachment import Attachment


class Message(Base):
    __tablename__ = "message"
    __table_args__ = (
        Index("ix_message_chat_id_id", "chat_id", "id"),
        Index("ix_message_text_trgm", "text", postgresql_using="gin", postgresql_ops={"text": "gin_trgm_ops"})
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    text: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    chat_id: Mapped[int] = mapped_column(ForeignKey("chat.id", ondelete="CASCADE"))
    sender_id: Mapped[int | None] = mapped_column(ForeignKey("user.id", ondelete="SET NULL"))
    sender: Mapped[User | None] = relationship(foreign_keys=[sender_id], passive_deletes=True, lazy="raise_on_sql")
    attachments: Mapped[list[Attachment]] = relationship(passive_deletes=True, lazy="raise_on_sql")

    def __repr__(self) -> str:
        return f"Message (id={self.id}), chat_id={self.chat_id})"
