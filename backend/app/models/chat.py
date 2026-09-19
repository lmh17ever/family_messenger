from datetime import datetime

from sqlalchemy import UniqueConstraint, ForeignKey, DateTime, func, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Chat(Base):
    __tablename__="chat"
    __table_args__ = (
        UniqueConstraint("user1_id", "user2_id", name="uq_chat_pair"),
        CheckConstraint("user1_id <= user2_id", name="ck_chat_users_order"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user1_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    user2_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(
            DateTime(timezone=True),
            server_default=func.now()
        )
    last_message_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True
        )
    messages: Mapped[list["Message"]] = relationship( # type: ignore
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Chat (id={self.id}, users={self.user1_id}<->{self.user2_id})"