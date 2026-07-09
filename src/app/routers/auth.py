from fastapi import APIRouter

from app import service
from app.auth import RefreshUserDependency
from app.database import SessionDependency
from app.schemas.auth import AccessTokenResponse, TokenResponse
from app.schemas.user import UserCreate, UserLogin, UserResponse

auth_router = APIRouter(prefix="/auth", tags=["auth"])

@auth_router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, session: SessionDependency):
    return await service.login(session=session, data=data)

@auth_router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: UserCreate, session: SessionDependency):
    return await service.register_user(session=session, data=data)

@auth_router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(user_id: RefreshUserDependency):
    return await service.refresh_access_token(user_id=user_id)
