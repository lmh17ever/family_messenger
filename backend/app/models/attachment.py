from sqlalchemy import Text, ForeignKey, DateTime, Index, func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from datetime import datetime

from app.db.base import Base


class Attachment(Base):
    __tablename__="attachment"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    message_id: Mapped[int] = mapped_column(ForeignKey("message.id"), index=True)

    def __repr__(self) -> str:
        return f"Message (id={self.id})"
