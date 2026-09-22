from fastapi import APIRouter

from app.api.routes.v1.endpoints.user import router as user_router
from app.api.routes.v1.endpoints.auth import router as auth_router
from app.api.routes.v1.endpoints.chat import router as chat_router
from app.api.routes.v1.endpoints.message import router as message_router
from app.api.routes.v1.endpoints.attachment import router as attachment_router


v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(user_router)
v1_router.include_router(auth_router)
v1_router.include_router(chat_router)
v1_router.include_router(message_router)
v1_router.include_router(attachment_router)
