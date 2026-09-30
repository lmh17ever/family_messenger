import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String, ForeignKey, DateTime, func, Index, Enum, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.message import Message
    from app.models.user import User

TITLE_LENGTH = 128
AVATAR_KEY_LENGTH = 1024
DIRECT_KEY_LENGTH = 32


class ChatType(enum.Enum):
    DIRECT = "direct"
    GROUP = "group"


def enum_values(enum_cls: type[enum.Enum]) -> list[str]:
    return [m.value for m in enum_cls]


class Chat(Base):
    __tablename__ = "chat"
    __table_args__ = (
        CheckConstraint(
            "(type = 'direct' AND direct_key IS NOT NULL AND title IS NULL) "
            "OR (type = 'group' AND direct_key IS NULL AND title IS NOT NULL)",
            "ck_chat_type_fields",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[ChatType] = mapped_column(
        Enum(ChatType, values_callable=enum_values),
        default=ChatType.DIRECT,
        server_default=ChatType.DIRECT.value
    )
    title: Mapped[str | None] = mapped_column(String(TITLE_LENGTH))  # Group only
    avatar_key: Mapped[str | None] = mapped_column(String(AVATAR_KEY_LENGTH))  # Group only
    direct_key: Mapped[str | None] = mapped_column(String(DIRECT_KEY_LENGTH), unique=True)  # "3_17",  Direct chat only
    creator_id: Mapped[int | None] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
            DateTime(timezone=True),
            server_default=func.now()
    )
    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        index=True
    )
    last_message_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("message.id", ondelete="SET NULL", use_alter=True, name="fk_chat_last_message"),
    )
    last_message: Mapped[Message | None] = relationship(
        foreign_keys="Chat.last_message_id",
        post_update=True,
        lazy="raise_on_sql"
    )
    members: Mapped[list[ChatMember]] = relationship(passive_deletes=True, lazy="raise_on_sql")


class ChatMember(Base):
    __tablename__ = "chat_member"
    __table_args__ = (Index("ix_chat_member_user_chat", "user_id", "chat_id"),)

    chat_id: Mapped[int] = mapped_column(ForeignKey("chat.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), primary_key=True)
    last_read_message_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("message.id", ondelete="SET NULL")
    )
    user: Mapped[User] = relationship(lazy="raise_on_sql")
