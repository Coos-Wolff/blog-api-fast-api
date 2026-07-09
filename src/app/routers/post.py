from fastapi import APIRouter

from app import service
from app.auth import CurrentUserDependency
from app.database import SessionDependency
from app.schemas.post import PostCreate, PostListResponse, PostResponse, PostUpdate

post_router = APIRouter(prefix="/post", tags=["posts"])

@post_router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, session: SessionDependency):
    return await service.get_post_by_id(session=session, post_id=post_id)

@post_router.get("/", response_model=PostListResponse)
async def list_posts(session: SessionDependency, page:int = 1, per_page: int = 5):
    return await service.get_all_posts(session=session, page=page, per_page=per_page)

@post_router.post("/add", response_model=PostResponse, status_code=201)
async def add_post(data: PostCreate, current_user_id: CurrentUserDependency, session: SessionDependency):
    return await service.add_post(session=session, data=data, current_user_id=current_user_id)

@post_router.patch("/{post_id}", response_model=PostResponse)
async def update_post(post_id: int, data: PostUpdate, current_user_id: CurrentUserDependency, session: SessionDependency):
    return await service.update_post(session=session, post_id=post_id, data=data, current_user_id=current_user_id)

@post_router.delete("/{post_id}", status_code=204)
async def delete_post(post_id: int, current_user_id: CurrentUserDependency, session: SessionDependency):
    await service.delete_post(session=session, post_id=post_id, current_user_id=current_user_id)



