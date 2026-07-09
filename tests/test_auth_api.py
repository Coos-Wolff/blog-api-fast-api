DEFAULT_USER = {"email": "jane@example.com", "name": "Jane Doe", "password": "super-strong-password"}

async def test_register_returns_201_and_user(client):
    response = await client.post("/auth/register", json=DEFAULT_USER)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == DEFAULT_USER["email"]
    assert body["name"] == DEFAULT_USER["name"]
    assert "password" not in body


async def test_register_duplicate_email_returns_409(client):
    await client.post("/auth/register", json=DEFAULT_USER)
    response = await client.post("/auth/register", json=DEFAULT_USER)

    assert response.status_code == 409


async def test_register_missing_fields_returns_422(client):
    response = await client.post("/auth/register", json={"email": "x@example.com"})

    assert response.status_code == 422


async def test_register_invalid_email_returns_422(client):
    response = await client.post(
        "/auth/register",
        json={"email": "not-an-email", "name": "X", "password": "pw"},
    )

    assert response.status_code == 422


async def test_login_returns_access_and_refresh_tokens(client):
    await client.post("/auth/register", json=DEFAULT_USER)
    response = await client.post(
        "/auth/login",
        json={"email": DEFAULT_USER["email"], "password": DEFAULT_USER["password"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body


async def test_login_wrong_password_returns_401(client):
    await client.post("/auth/register", json=DEFAULT_USER)
    response = await client.post(
        "/auth/login",
        json={"email": DEFAULT_USER["email"], "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["error"] == "Invalid email or password"


async def test_login_unknown_email_returns_401_identical_message(client):
    response = await client.post(
        "/auth/login",
        json={"email": "nobody@example.com", "password": "whatever"},
    )

    assert response.status_code == 401
    assert response.json()["error"] == "Invalid email or password"


async def test_login_missing_fields_returns_422(client):
    response = await client.post("/auth/login", json={"email": DEFAULT_USER["email"]})

    assert response.status_code == 422


async def test_refresh_with_refresh_token_returns_new_access_token(client):
    await client.post("/auth/register", json=DEFAULT_USER)
    login = await client.post(
        "/auth/login",
        json={"email": DEFAULT_USER["email"], "password": DEFAULT_USER["password"]},
    )
    refresh_token = login.json()["refresh_token"]

    response = await client.post(
        "/auth/refresh",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )

    assert response.status_code == 200
    assert "access_token" in response.json()


async def test_refresh_with_access_token_returns_401(client):
    await client.post("/auth/register", json=DEFAULT_USER)
    login = await client.post(
        "/auth/login",
        json={"email": DEFAULT_USER["email"], "password": DEFAULT_USER["password"]},
    )
    access_token = login.json()["access_token"]

    response = await client.post(
        "/auth/refresh",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 401


async def test_refresh_without_token_returns_401_or_403(client):
    response = await client.post("/auth/refresh")

    assert response.status_code in (401, 403)