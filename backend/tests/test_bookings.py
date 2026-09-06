"""Ключевые проверки поведения на границах: пересечения, стык, валидация допов."""


def booking_payload(room_id, start, end, **extra):
    return {
        "room_id": room_id,
        "title": extra.pop("title", "Meeting"),
        "start_time": f"2026-10-01T{start}:00+00:00",
        "end_time": f"2026-10-01T{end}:00+00:00",
        **extra,
    }


async def test_create_booking(client, user_headers, room):
    resp = await client.post(
        "/bookings", headers=user_headers, json=booking_payload(room["id"], "14:00", "15:00")
    )
    assert resp.status_code == 201
    assert resp.json()["room_id"] == room["id"]


async def test_overlapping_booking_conflicts(client, user_headers, room):
    first = await client.post(
        "/bookings", headers=user_headers, json=booking_payload(room["id"], "14:00", "15:00")
    )
    assert first.status_code == 201
    # Пересечение 14:30–15:30 с существующей 14:00–15:00.
    second = await client.post(
        "/bookings", headers=user_headers, json=booking_payload(room["id"], "14:30", "15:30")
    )
    assert second.status_code == 409


async def test_adjacent_booking_allowed(client, user_headers, room):
    await client.post(
        "/bookings", headers=user_headers, json=booking_payload(room["id"], "14:00", "15:00")
    )
    # Встык 15:00–16:00 — не пересечение (интервал полуоткрытый).
    resp = await client.post(
        "/bookings", headers=user_headers, json=booking_payload(room["id"], "15:00", "16:00")
    )
    assert resp.status_code == 201


async def test_end_before_start_rejected(client, user_headers, room):
    resp = await client.post(
        "/bookings", headers=user_headers, json=booking_payload(room["id"], "15:00", "14:00")
    )
    assert resp.status_code == 422


async def test_unknown_amenity_rejected(client, user_headers, room):
    resp = await client.post(
        "/bookings",
        headers=user_headers,
        json=booking_payload(room["id"], "14:00", "15:00", amenities=["water", "gold"]),
    )
    assert resp.status_code == 422


async def test_amenities_and_comment_round_trip(client, user_headers, room):
    resp = await client.post(
        "/bookings",
        headers=user_headers,
        json=booking_payload(
            room["id"], "14:00", "15:00",
            amenities=["coffee", "water", "coffee"], comment="near window",
        ),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["comment"] == "near window"
    assert body["amenities"] == ["coffee", "water"]  # дубли убраны, отсортировано


async def test_booking_unknown_room_404(client, user_headers):
    resp = await client.post(
        "/bookings", headers=user_headers, json=booking_payload(9999, "14:00", "15:00")
    )
    assert resp.status_code == 404


async def test_cannot_cancel_others_booking(client, user_headers, room):
    created = await client.post(
        "/bookings", headers=user_headers, json=booking_payload(room["id"], "14:00", "15:00")
    )
    booking_id = created.json()["id"]

    # Второй обычный пользователь не может отменить чужую бронь.
    await client.post(
        "/auth/register",
        json={"email": "other@test.com", "full_name": "Other", "password": "secret123"},
    )
    login = await client.post(
        "/auth/login", data={"username": "other@test.com", "password": "secret123"}
    )
    other = {"Authorization": f"Bearer {login.json()['access_token']}"}
    resp = await client.delete(f"/bookings/{booking_id}", headers=other)
    assert resp.status_code == 403


async def test_admin_can_cancel_any_booking(client, user_headers, admin_headers, room):
    created = await client.post(
        "/bookings", headers=user_headers, json=booking_payload(room["id"], "14:00", "15:00")
    )
    booking_id = created.json()["id"]
    resp = await client.delete(f"/bookings/{booking_id}", headers=admin_headers)
    assert resp.status_code == 204
