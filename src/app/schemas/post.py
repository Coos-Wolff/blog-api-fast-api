from datetime import date
from pydantic import BaseModel, ConfigDict

class PostCreate(BaseModel):
    title: str
    subtitle: str
    date: date
    body: str
    img_url: str

class PostUpdate(BaseModel):
    title: str | None = None
    subtitle: str | None = None
    date: date | None = None
    body: str | None = None
    img_url: str | None = None

class AuthorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str

class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    subtitle: str
    date: date
    body: str
    img_url: str
    author: AuthorResponse

class PostListResponse(BaseModel):
    items: list[PostResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
