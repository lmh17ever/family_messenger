from sqlalchemy import String, false, true
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


from app.db.base import Base


USERNAME_LENGTH = 30
AVATAR_KEY_LENGTH = 1024


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(USERNAME_LENGTH), unique=True, index=True)
    avatar_key: Mapped[str | None] = mapped_column(String(AVATAR_KEY_LENGTH))
    hashed_password: Mapped[str]
    is_active: Mapped[bool] = mapped_column(server_default=true())
    is_superuser: Mapped[bool] = mapped_column(server_default=false(), default=False)

    def __repr__(self) -> str:
        return f"User (id={self.id}, username={self.username})"
