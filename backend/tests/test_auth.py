async def test_register_and_me(client):
    resp = await client.post(
        "/auth/register",
        json={"email": "a@test.com", "full_name": "Alice", "password": "secret123"},
    )
    assert resp.status_code == 201
    assert resp.json()["role"] == "user"
    assert "hashed_password" not in resp.json()

    login = await client.post(
        "/auth/login", data={"username": "a@test.com", "password": "secret123"}
    )
    token = login.json()["access_token"]
    me = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "a@test.com"


async def test_duplicate_email_conflict(client):
    payload = {"email": "dup@test.com", "full_name": "Dup", "password": "secret123"}
    assert (await client.post("/auth/register", json=payload)).status_code == 201
    assert (await client.post("/auth/register", json=payload)).status_code == 409


async def test_login_wrong_password(client):
    await client.post(
        "/auth/register",
        json={"email": "b@test.com", "full_name": "Bob", "password": "secret123"},
    )
    resp = await client.post(
        "/auth/login", data={"username": "b@test.com", "password": "wrong"}
    )
    assert resp.status_code == 401


async def test_me_requires_auth(client):
    assert (await client.get("/auth/me")).status_code == 401
