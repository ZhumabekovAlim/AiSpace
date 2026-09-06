async def test_regular_user_cannot_create_room(client, user_headers):
    resp = await client.post(
        "/rooms", headers=user_headers, json={"name": "X", "capacity": 4}
    )
    assert resp.status_code == 403


async def test_admin_creates_room(client, admin_headers):
    resp = await client.post(
        "/rooms", headers=admin_headers, json={"name": "Big", "capacity": 12}
    )
    assert resp.status_code == 201
    assert resp.json()["is_active"] is True


async def test_duplicate_room_name_conflict(client, admin_headers):
    await client.post("/rooms", headers=admin_headers, json={"name": "Dup", "capacity": 4})
    resp = await client.post(
        "/rooms", headers=admin_headers, json={"name": "Dup", "capacity": 4}
    )
    assert resp.status_code == 409


async def test_admin_updates_room(client, admin_headers, room):
    resp = await client.patch(
        f"/rooms/{room['id']}", headers=admin_headers, json={"capacity": 20}
    )
    assert resp.status_code == 200
    assert resp.json()["capacity"] == 20


async def test_soft_delete_hides_room_but_keeps_it(client, admin_headers, room):
    # Архивируем.
    resp = await client.delete(f"/rooms/{room['id']}", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False

    # Пропала из обычного списка.
    default = await client.get("/rooms", headers=admin_headers)
    assert all(r["id"] != room["id"] for r in default.json())

    # Но видна с include_inactive и может быть возвращена.
    full = await client.get("/rooms?include_inactive=true", headers=admin_headers)
    assert any(r["id"] == room["id"] for r in full.json())

    restored = await client.patch(
        f"/rooms/{room['id']}", headers=admin_headers, json={"is_active": True}
    )
    assert restored.json()["is_active"] is True


async def test_include_inactive_ignored_for_regular_user(client, user_headers, admin_headers, room):
    await client.delete(f"/rooms/{room['id']}", headers=admin_headers)
    # Обычный юзер не видит архивные даже с флагом.
    resp = await client.get("/rooms?include_inactive=true", headers=user_headers)
    assert all(r["id"] != room["id"] for r in resp.json())
