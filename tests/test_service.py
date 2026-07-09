from unittest.mock import Mock, AsyncMock

import pytest

from app import service
from app.exceptions import (
    ForbiddenError,
    UnauthorizedError,
    NotFoundError,
    PostTitleAlreadyExistsError,
    EmailAlreadyExistsError,
    InvalidCredentialsError,
)
from app.schemas.post import PostUpdate
from app.service import INVALID_LOGIN_MESSAGE
from tests.util_test import create_user_id

async def test_require_ownership_unauthorized_when_user_missing(monkeypatch):
    monkeypatch.setattr(service.repository, "find_user_by_id", AsyncMock(return_value=None))

    with pytest.raises(UnauthorizedError):
        await service.require_ownership(session=None, post_id=1, current_user_id=1)

async def test_require_ownership_not_found_when_post_missing(monkeypatch):
    fake_user = Mock()
    fake_user.id = 1
    fake_user.is_admin = False
    monkeypatch.setattr(service.repository, "find_user_by_id", AsyncMock(return_value=fake_user))
    monkeypatch.setattr(service.repository, "get_post_by_id", AsyncMock(return_value=None))

    with pytest.raises(NotFoundError):
        await service.require_ownership(session=None, post_id=1, current_user_id=fake_user.id)

async def test_require_ownership_forbidden_for_non_owner_non_admin(monkeypatch):
    fake_user = Mock()
    fake_user.id = 1
    fake_user.is_admin = False
    fake_post = Mock()
    fake_post.author_id = 2  # owned by someone else
    monkeypatch.setattr(service.repository, "find_user_by_id", AsyncMock(return_value=fake_user))
    monkeypatch.setattr(service.repository, "get_post_by_id", AsyncMock(return_value=fake_post))

    with pytest.raises(ForbiddenError):
        await service.require_ownership(session=None, post_id=99, current_user_id=fake_user.id)

async def test_require_ownership_allows_author(monkeypatch):
    fake_user = Mock()
    fake_user.id = 1
    fake_user.is_admin = False
    fake_post = Mock()
    fake_post.author_id = 1
    monkeypatch.setattr(service.repository, "find_user_by_id", AsyncMock(return_value=fake_user))
    monkeypatch.setattr(service.repository, "get_post_by_id", AsyncMock(return_value=fake_post))

    await service.require_ownership(session=None, post_id=1, current_user_id=1)

async def test_require_ownership_allows_admin_on_others_post(monkeypatch):
    fake_user = Mock()
    fake_user.id = 1
    fake_user.is_admin = True
    fake_post = Mock()
    fake_post.author_id = 2
    monkeypatch.setattr(service.repository, "find_user_by_id", AsyncMock(return_value=fake_user))
    monkeypatch.setattr(service.repository, "get_post_by_id", AsyncMock(return_value=fake_post))

    await service.require_ownership(session=None, post_id=99, current_user_id=1)

async def test_get_post_by_id_not_found(monkeypatch):
    monkeypatch.setattr(service.repository, "get_post_by_id", AsyncMock(return_value=None))

    with pytest.raises(NotFoundError):
        await service.get_post_by_id(session=None, post_id=1)

async def test_get_all_posts_pagination_math(monkeypatch):
    monkeypatch.setattr(service.repository, "get_all_posts", AsyncMock(return_value=([], 47)))

    result = await service.get_all_posts(session=None, page=1, per_page=5)

    assert result.total == 47
    assert result.total_pages == 10
    assert result.page == 1
    assert result.per_page == 5

async def test_get_all_posts_exact_multiple(monkeypatch):
    monkeypatch.setattr(service.repository, "get_all_posts", AsyncMock(return_value=([], 20)))

    result = await service.get_all_posts(session=None, page=1, per_page=5)

    assert result.total_pages == 4

async def test_add_post_duplicate_title(monkeypatch):
    fake_data = Mock()
    fake_data.title = "Existing Title"
    monkeypatch.setattr(service.repository, "find_post_by_title", AsyncMock(return_value=Mock()))

    with pytest.raises(PostTitleAlreadyExistsError):
        await service.add_post(session=None, data=fake_data, current_user_id=create_user_id())

async def test_update_post_duplicate_title_different_post(monkeypatch):
    fake_user = Mock()
    fake_user.id = 1
    fake_user.is_admin = False
    fake_post = Mock()
    fake_post.author_id = 1
    monkeypatch.setattr(service.repository, "find_user_by_id", AsyncMock(return_value=fake_user))
    monkeypatch.setattr(service.repository, "get_post_by_id", AsyncMock(return_value=fake_post))

    other_post = Mock()
    other_post.id = 99
    monkeypatch.setattr(service.repository, "find_post_by_title", AsyncMock(return_value=other_post))

    data = PostUpdate(title="Taken Title")
    with pytest.raises(PostTitleAlreadyExistsError):
        await service.update_post(session=None, post_id=1, current_user_id=1, data=data)

async def test_register_user_duplicate_email(monkeypatch):
    monkeypatch.setattr(service.repository, "find_user_by_email", AsyncMock(return_value=Mock()))
    fake_data = Mock()
    fake_data.email = "taken@example.com"

    with pytest.raises(EmailAlreadyExistsError):
        await service.register_user(session=None, data=fake_data)

async def test_login_unknown_email_raises_with_vague_message(monkeypatch):
    monkeypatch.setattr(service.repository, "find_user_by_email", AsyncMock(return_value=None))
    monkeypatch.setattr(service.security, "verify_password", Mock(return_value=False))
    data = Mock()
    data.email = "nobody@example.com"
    data.password = "whatever"

    with pytest.raises(InvalidCredentialsError) as exc_info:
        await service.login(session=None, data=data)

    assert str(exc_info.value) == INVALID_LOGIN_MESSAGE

async def test_login_wrong_password_raises_with_vague_message(monkeypatch):
    fake_user = Mock()
    fake_user.password = "stored-hash"
    monkeypatch.setattr(service.repository, "find_user_by_email", AsyncMock(return_value=fake_user))
    monkeypatch.setattr(service.security, "verify_password", Mock(return_value=False))
    data = Mock()
    data.email = "someone@example.com"
    data.password = "wrong"

    with pytest.raises(InvalidCredentialsError) as exc_info:
        await service.login(session=None, data=data)

    assert str(exc_info.value) == INVALID_LOGIN_MESSAGE


async def test_login_unknown_email_still_runs_dummy_hash(monkeypatch):
    monkeypatch.setattr(service.repository, "find_user_by_email", AsyncMock(return_value=None))
    verify_mock = Mock(return_value=False)
    monkeypatch.setattr(service.security, "verify_password", verify_mock)
    data = Mock()
    data.email = "nobody@example.com"
    data.password = "whatever"

    with pytest.raises(InvalidCredentialsError):
        await service.login(session=None, data=data)

    verify_mock.assert_called_once()