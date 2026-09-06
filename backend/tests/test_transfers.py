"""Передача брони между пользователями."""
import pytest_asyncio


def payload(room_id, start, end, **extra):
    return {
        "room_id": room_id,
        "title": extra.pop("title", "Meeting"),
        "start_time": f"2026-11-01T{start}:00+00:00",
        "end_time": f"2026-11-01T{end}:00+00:00",
        **extra,
    }


@pytest_asyncio.fixture
async def user2_headers(client):
    await client.post(
        "/auth/register",
        json={"email": "u2@test.com", "full_name": "Second", "password": "secret123"},
    )
    login = await client.post(
        "/auth/login", data={"username": "u2@test.com", "password": "secret123"}
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def _book(client, headers, room_id, start="10:00", end="11:00"):
    resp = await client.post("/bookings", headers=headers, json=payload(room_id, start, end))
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def test_request_transfer(client, user_headers, user2_headers, room):
    booking_id = await _book(client, user_headers, room["id"])
    resp = await client.post(
        "/transfers", headers=user2_headers, json={"booking_id": booking_id}
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "pending"


async def test_cannot_request_own_booking(client, user_headers, room):
    booking_id = await _book(client, user_headers, room["id"])
    resp = await client.post(
        "/transfers", headers=user_headers, json={"booking_id": booking_id}
    )
    assert resp.status_code == 400


async def test_duplicate_request_rejected(client, user_headers, user2_headers, room):
    booking_id = await _book(client, user_headers, room["id"])
    body = {"booking_id": booking_id}
    assert (await client.post("/transfers", headers=user2_headers, json=body)).status_code == 201
    assert (await client.post("/transfers", headers=user2_headers, json=body)).status_code == 400


async def test_accept_transfers_ownership_and_applies_changes(
    client, user_headers, user2_headers, room
):
    booking_id = await _book(client, user_headers, room["id"])
    created = await client.post(
        "/transfers",
        headers=user2_headers,
        json={
            "booking_id": booking_id,
            "new_title": "Handed over",
            "new_amenities": ["coffee"],
        },
    )
    transfer_id = created.json()["id"]

    # Владелец (user1) подтверждает.
    accepted = await client.post(f"/transfers/{transfer_id}/accept", headers=user_headers)
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "accepted"

    # Бронь теперь у user2, с применёнными изменениями (видно в истории админа).
    who = await client.get("/auth/me", headers=user2_headers)
    user2_id = who.json()["id"]
    mine = await client.get("/bookings/my", headers=user2_headers)
    b = next(x for x in mine.json() if x["id"] == booking_id)
    assert b["title"] == "Handed over"
    assert b["amenities"] == ["coffee"]
    assert b["user_id"] == user2_id


async def test_only_owner_can_accept(client, user_headers, user2_headers, room):
    booking_id = await _book(client, user_headers, room["id"])
    created = await client.post(
        "/transfers", headers=user2_headers, json={"booking_id": booking_id}
    )
    transfer_id = created.json()["id"]
    # Запросивший не может сам подтвердить.
    resp = await client.post(f"/transfers/{transfer_id}/accept", headers=user2_headers)
    assert resp.status_code == 403


async def test_owner_rejects(client, user_headers, user2_headers, room):
    booking_id = await _book(client, user_headers, room["id"])
    created = await client.post(
        "/transfers", headers=user2_headers, json={"booking_id": booking_id}
    )
    transfer_id = created.json()["id"]
    resp = await client.post(f"/transfers/{transfer_id}/reject", headers=user_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"


async def test_accept_with_conflicting_new_time_409(
    client, user_headers, user2_headers, room
):
    # Две брони user1: 10-11 и 12-13.
    target = await _book(client, user_headers, room["id"], "10:00", "11:00")
    await _book(client, user_headers, room["id"], "12:00", "13:00")

    # user2 просит первую, но со временем, пересекающим вторую (12:30-12:45).
    created = await client.post(
        "/transfers",
        headers=user2_headers,
        json={
            "booking_id": target,
            "new_start_time": "2026-11-01T12:30:00+00:00",
            "new_end_time": "2026-11-01T12:45:00+00:00",
        },
    )
    transfer_id = created.json()["id"]
    resp = await client.post(f"/transfers/{transfer_id}/accept", headers=user_headers)
    assert resp.status_code == 409
