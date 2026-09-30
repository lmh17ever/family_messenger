from fastapi import WebSocket, Depends
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.session import get_session
from app.core.config import settings
from app.models.user import User
from app.core.security import jwt
from app.schemas.token import TokenData

async def get_websocket_user(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_session)
) -> User | None:
    token = websocket.query_params.get("token")
    authorization = websocket.headers.get("authorization", "")

    if not token and authorization.lower().startswith("bearer "):
        token = authorization[7:]
    if not token:
        return None

    try:
        payload = jwt.decode(
            token,
            settings.JWT_ACCESS_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        subject = payload.get("sub")
        if not isinstance(subject, str) or payload.get("refresh", False):
            return None
        token_data = TokenData.model_validate({"user_id": subject})
    except ValidationError:
        return None
    except InvalidTokenError:
        return None

    return await db.scalar(select(User).where(User.id == token_data.user_id))
