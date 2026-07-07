import datetime

from app.database import Base
from sqlalchemy import Integer, String, Text, ForeignKey, Boolean, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

class BlogPost(Base):
    __tablename__ = "blog_post"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    author: Mapped["User"] = relationship(back_populates="posts")
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String (20), nullable=False)
    password: Mapped[str] = mapped_column(Text, nullable=False)
    posts: Mapped[list["BlogPost"]] = relationship(back_populates="author")
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)