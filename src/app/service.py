import math

from sqlalchemy.ext.asyncio import AsyncSession

from app import repository, security
from app.exceptions import (
    EmailAlreadyExistsError,
    ForbiddenError,
    InvalidCredentialsError,
    NotFoundError,
    PostTitleAlreadyExistsError,
    UnauthorizedError,
)
from app.models import BlogPost, User
from app.schemas.auth import AccessTokenResponse, TokenResponse
from app.schemas.post import PostCreate, PostListResponse, PostResponse, PostUpdate
from app.schemas.user import UserCreate, UserLogin, UserResponse

DUMMY_HASH = security.hash_password("Very.Long.Dummy.Hash.14232!")
INVALID_LOGIN_MESSAGE = "Invalid email or password"
async def get_all_posts(session: AsyncSession, page: int, per_page: int) -> PostListResponse:
    posts, total = await repository.get_all_posts(session=session, per_page=per_page, page=page)
    total_pages = math.ceil(total / per_page) if per_page else 0
    return PostListResponse(
        items=posts,
        total=total,
        total_pages=total_pages,
        per_page=per_page,
        page=page
    )

async def get_post_by_id(session: AsyncSession, post_id: int) -> PostResponse:
    post = await repository.get_post_by_id(session=session, post_id=post_id)
    if post is None:
        raise NotFoundError(f"No post found for [{post_id}]")
    return PostResponse.model_validate(post)

async def require_ownership(session: AsyncSession, post_id: int, current_user_id: int):
    user = await repository.find_user_by_id(session=session, user_id=current_user_id)
    if user is None:
        raise UnauthorizedError("No user found")
    post = await repository.get_post_by_id(session=session, post_id=post_id)
    if post is None:
        raise NotFoundError(f"No post found for [{post_id}]")
    if post.author_id != current_user_id and not user.is_admin:
        raise ForbiddenError("Not allowed to make modifications")

async def add_post(session: AsyncSession, data: PostCreate, current_user_id: int) -> PostResponse:
    if await repository.find_post_by_title(session=session, title=data.title):
        raise PostTitleAlreadyExistsError("Post title already exists")
    post = BlogPost(**data.model_dump(), author_id=current_user_id)
    created = await repository.add_post(session=session, post=post)
    return PostResponse.model_validate(created)

async def update_post(session: AsyncSession, post_id: int, current_user_id: int, data: PostUpdate) -> PostResponse:
    await require_ownership(session=session, post_id=post_id, current_user_id=current_user_id)
    fields = data.model_dump(exclude_unset=True)
    if "title" in fields:
        existing = await repository.find_post_by_title(session=session, title=fields["title"])
        if existing and existing.id != post_id:
            raise PostTitleAlreadyExistsError("Post title already exists")
    updated = await repository.patch_post(session=session, post_id=post_id, fields=fields)
    return PostResponse.model_validate(updated)

async def delete_post(session: AsyncSession, post_id: int, current_user_id: int):
    await require_ownership(session=session, post_id=post_id, current_user_id=current_user_id)
    await repository.delete_post(session=session, post_id=post_id)

async def register_user(session: AsyncSession, data: UserCreate) -> UserResponse:
    email = data.email
    user = await repository.find_user_by_email(session=session, email=email)
    if user:
        raise EmailAlreadyExistsError("Email already exists")

    hashed_password = security.hash_password(password=data.password)
    new_user = User(
        email=email,
        name=data.name,
        password=hashed_password
    )
    registered_user = await repository.add_user(session=session, user=new_user)
    return UserResponse.model_validate(registered_user)

async def login(session: AsyncSession, data: UserLogin) -> TokenResponse:
    user = await repository.find_user_by_email(session=session, email=data.email)
    if user is None:
        _ = security.verify_password(password=data.password, hashed=DUMMY_HASH)
        raise InvalidCredentialsError(INVALID_LOGIN_MESSAGE)
    is_valid = security.verify_password(password=data.password, hashed=user.password)
    if not is_valid:
        raise InvalidCredentialsError(INVALID_LOGIN_MESSAGE)

    tokens = {
        "access_token":security.create_access_token(user_id=user.id),
        "refresh_token":security.create_refresh_token(user_id=user.id)
    }
    return TokenResponse(access_token=tokens["access_token"], refresh_token=tokens["refresh_token"])

async def refresh_access_token(user_id: int) -> AccessTokenResponse:
    return AccessTokenResponse(access_token=security.create_access_token(user_id=user_id))