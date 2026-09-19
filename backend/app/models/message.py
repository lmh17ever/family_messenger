from sqlalchemy import Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from datetime import datetime

from app.db.base import Base


class Message(Base):
    __tablename__="message"

    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chat.id", ondelete="CASCADE"))
    sender_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))

    def __repr__(self) -> str:
        return f"Message (id={self.id})"
