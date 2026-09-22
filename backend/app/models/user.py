from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


from app.db.base import Base


class User(Base):
    __tablename__="user"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    avatar_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    hashed_password: Mapped[str]
    is_active: Mapped[bool] = mapped_column(server_default="true")
    is_superuser: Mapped[bool] = mapped_column(server_default="false")

    def set_hash_password(self, hashed_password):
        self.hashed_password = hashed_password

    def __repr__(self) -> str:
        return f"User (id={self.id}, nickname={self.username})"
