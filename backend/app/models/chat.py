from enum import StrEnum
from datetime import datetime

from sqlalchemy import BigInteger, String, UniqueConstraint, ForeignKey, DateTime, func, CheckConstraint, Index, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ChatType(StrEnum):
    DIRECT = "direct"
    GROUP = "group"


class Chat(Base):
    __tablename__ = "chat"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[ChatType] = mapped_column(
        Enum(ChatType, name="chat_type", values_callable=lambda e: [m.value for m in e]),
        default=ChatType.DIRECT,
    )
    title: Mapped[str | None] = mapped_column(String(128)) # Group only
    avatar_key: Mapped[str | None] = mapped_column(String(1024), nullable=True) # Group only
    direct_key: Mapped[str | None] = mapped_column(unique=True) # "3_17",  Direct chat only
    creator_id: Mapped[int | None] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
            DateTime(timezone=True),
            server_default=func.now()
        )
    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True
        )
    last_message_id: Mapped[int | None] = mapped_column(
        ForeignKey("message.id", ondelete="SET NULL", use_alter=True, name="fk_chat_last_message"),
        nullable=True
    )
    last_message: Mapped["Message | None"] = relationship( # type: ignore
        foreign_keys="Chat.last_message_id",
        post_update=True
    )
    members: Mapped[list["ChatMember"]] = relationship()


class ChatMember(Base):
    __tablename__ = "chat_member"
    __table_args__ = (Index("ix_chat_member_user_chat", "user_id", "chat_id"),)

    chat_id: Mapped[int] = mapped_column(ForeignKey("chat.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), primary_key=True)
    last_read_message_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("message.id", ondelete="SET NULL")
    )
    user: Mapped["User"] = relationship()
