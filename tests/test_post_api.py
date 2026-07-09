VALID_POST = {
    "title": "My First Post",
    "subtitle": "A subtitle",
    "date": "2026-07-01",
    "body": "This is a post body.",
    "img_url": "https://example.com/image.jpg",
}

SECOND_USER = {"email": "bob@example.com", "name": "Bob", "password": "another-strong-password"}


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _create_post(client, token, overrides=None):
    payload = {**VALID_POST, **(overrides or {})}
    response = await client.post("/post/add", json=payload, headers=auth_header(token))
    return response


async def _second_user_token(client):
    await client.post("/auth/register", json=SECOND_USER)
    login = await client.post(
        "/auth/login",
        json={"email": SECOND_USER["email"], "password": SECOND_USER["password"]},
    )
    return login.json()["access_token"]


async def test_add_post_returns_201_with_nested_author(client, auth_token):
    response = await _create_post(client, auth_token)

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == VALID_POST["title"]
    assert body["author"]["name"] == "Jane Doe"
    assert "author_id" not in body


async def test_add_post_without_token_returns_401_or_403(client):
    response = await client.post("/post/add", json=VALID_POST)

    assert response.status_code in (401, 403)


async def test_add_post_duplicate_title_returns_409(client, auth_token):
    await _create_post(client, auth_token)
    response = await _create_post(client, auth_token)  # same title again

    assert response.status_code == 409


async def test_add_post_missing_fields_returns_422(client, auth_token):
    response = await client.post("/post/add", json={"title": "only title"}, headers=auth_header(auth_token))

    assert response.status_code == 422


async def test_add_post_invalid_date_returns_422(client, auth_token):
    response = await _create_post(client, auth_token, overrides={"date": "not-a-date"})

    assert response.status_code == 422


async def test_get_post_by_id_returns_200(client, auth_token):
    created = await _create_post(client, auth_token)
    post_id = created.json()["id"]

    response = await client.get(f"/post/{post_id}")

    assert response.status_code == 200
    assert response.json()["id"] == post_id


async def test_get_post_by_id_missing_returns_404(client):
    response = await client.get("/post/9999")

    assert response.status_code == 404


async def test_get_post_by_id_non_integer_returns_422(client):
    response = await client.get("/post/not-an-int")

    assert response.status_code == 422


async def test_list_posts_returns_pagination_metadata(client, auth_token):
    await _create_post(client, auth_token, overrides={"title": "Post A"})
    await _create_post(client, auth_token, overrides={"title": "Post B"})

    response = await client.get("/post/")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["page"] == 1
    assert body["per_page"] == 5
    assert body["total_pages"] == 1
    assert len(body["items"]) == 2


async def test_update_post_as_owner_returns_200(client, auth_token):
    created = await _create_post(client, auth_token)
    post_id = created.json()["id"]

    response = await client.patch(
        f"/post/{post_id}",
        json={"body": "Updated body"},
        headers=auth_header(auth_token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["body"] == "Updated body"
    assert body["title"] == VALID_POST["title"]


async def test_update_post_as_non_owner_returns_403(client, auth_token):
    created = await _create_post(client, auth_token)
    post_id = created.json()["id"]

    other_token = await _second_user_token(client)
    response = await client.patch(
        f"/post/{post_id}",
        json={"body": "Hijacked"},
        headers=auth_header(other_token),
    )

    assert response.status_code == 403


async def test_update_post_missing_returns_404(client, auth_token):
    response = await client.patch(
        "/post/9999",
        json={"body": "x"},
        headers=auth_header(auth_token),
    )

    assert response.status_code == 404


async def test_update_post_without_token_returns_401_or_403(client, auth_token):
    created = await _create_post(client, auth_token)
    post_id = created.json()["id"]

    response = await client.patch(f"/post/{post_id}", json={"body": "x"})

    assert response.status_code in (401, 403)


async def test_delete_post_as_owner_returns_204(client, auth_token):
    created = await _create_post(client, auth_token)
    post_id = created.json()["id"]

    response = await client.delete(f"/post/{post_id}", headers=auth_header(auth_token))

    assert response.status_code == 204
    follow_up = await client.get(f"/post/{post_id}")
    assert follow_up.status_code == 404


async def test_delete_post_as_non_owner_returns_403(client, auth_token):
    created = await _create_post(client, auth_token)
    post_id = created.json()["id"]

    other_token = await _second_user_token(client)
    response = await client.delete(f"/post/{post_id}", headers=auth_header(other_token))

    assert response.status_code == 403


async def test_delete_post_missing_returns_404(client, auth_token):
    response = await client.delete("/post/9999", headers=auth_header(auth_token))

    assert response.status_code == 404


async def test_delete_post_without_token_returns_401_or_403(client, auth_token):
    created = await _create_post(client, auth_token)
    post_id = created.json()["id"]

    response = await client.delete(f"/post/{post_id}")

    assert response.status_code in (401, 403)