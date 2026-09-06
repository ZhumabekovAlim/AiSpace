async def test_regular_user_cannot_list_users(client, user_headers):
    assert (await client.get("/users", headers=user_headers)).status_code == 403


async def test_admin_lists_users_with_counts(client, admin_headers, user_headers):
    resp = await client.get("/users", headers=admin_headers)
    assert resp.status_code == 200
    emails = {u["email"] for u in resp.json()}
    assert {"admin@test.com", "user@test.com"} <= emails
    assert all("bookings_count" in u for u in resp.json())


async def test_admin_changes_user_role(client, admin_headers, user_headers):
    users = (await client.get("/users", headers=admin_headers)).json()
    target = next(u for u in users if u["email"] == "user@test.com")
    resp = await client.patch(
        f"/users/{target['id']}", headers=admin_headers, json={"role": "admin"}
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "admin"


async def test_admin_cannot_lock_self(client, admin_headers):
    me = (await client.get("/auth/me", headers=admin_headers)).json()
    resp = await client.patch(
        f"/users/{me['id']}", headers=admin_headers, json={"is_active": False}
    )
    assert resp.status_code == 400


async def test_analytics_requires_admin(client, user_headers):
    assert (await client.get("/analytics", headers=user_headers)).status_code == 403


async def test_analytics_summary_shape(client, admin_headers):
    resp = await client.get("/analytics", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    for key in (
        "total_bookings",
        "upcoming_bookings",
        "active_rooms",
        "total_users",
        "total_hours",
        "per_room",
        "per_day",
        "top_users",
        "amenities",
    ):
        assert key in body
    assert len(body["per_day"]) == 14  # окно ±неделя


async def test_admin_history_lists_all_bookings(client, admin_headers, user_headers, room):
    await client.post(
        "/bookings",
        headers=user_headers,
        json={
            "room_id": room["id"],
            "title": "Standup",
            "start_time": "2026-10-02T09:00:00+00:00",
            "end_time": "2026-10-02T09:30:00+00:00",
        },
    )
    resp = await client.get("/bookings/all", headers=admin_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    item = resp.json()[0]
    assert item["room_name"] == room["name"]
    assert item["user"]["email"] == "user@test.com"


async def test_regular_user_cannot_see_history(client, user_headers):
    assert (await client.get("/bookings/all", headers=user_headers)).status_code == 403
