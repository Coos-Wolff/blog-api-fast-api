from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app import service
from app.database import get_db
from app.schemas.post import PostResponse, PostListResponse

router = APIRouter(prefix="/post", tags=["posts"])

@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, session: AsyncSession = Depends(get_db)):
    return await service.get_post_by_id(session=session, post_id=post_id)

@router.get("/", response_model=PostListResponse)
async def list_posts(page:int = 1, per_page: int = 5, session: AsyncSession = Depends(get_db)):
    return await service.get_all_posts(session=session, page=page, per_page=per_page)

