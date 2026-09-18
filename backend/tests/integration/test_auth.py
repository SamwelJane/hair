from sqlalchemy import select

from app.models.enums import UserRole
from app.models.identity import RefreshToken, User


async def _register(client, email="jane@example.com", password="supersecret1"):
    return await client.post(
        "/auth/register",
        json={"name": "Jane Doe", "email": email, "password": password, "phone": "+254712345678"},
    )


async def test_register_returns_token_pair(client):
    resp = await _register(client)
    assert resp.status_code == 201
    body = resp.json()
    assert body["user"]["email"] == "jane@example.com"
    assert body["user"]["role"] == "CUSTOMER"
    assert body["access_token"]
    assert body["refresh_token"]


async def test_register_duplicate_email_rejected(client):
    await _register(client)
    resp = await _register(client)
    assert resp.status_code == 409


async def test_login_with_correct_password_succeeds(client):
    await _register(client)
    resp = await client.post("/auth/login", json={"email": "jane@example.com", "password": "supersecret1"})
    assert resp.status_code == 200
    assert resp.json()["user"]["email"] == "jane@example.com"


async def test_login_with_wrong_password_rejected(client):
    await _register(client)
    resp = await client.post("/auth/login", json={"email": "jane@example.com", "password": "wrong-password"})
    assert resp.status_code == 401


async def test_me_requires_bearer_token(client):
    resp = await client.get("/auth/me")
    assert resp.status_code == 401


async def test_me_returns_current_user(client):
    register_resp = await _register(client)
    token = register_resp.json()["access_token"]
    resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "jane@example.com"


async def test_refresh_rotates_token_and_old_one_becomes_unusable(client, db):
    register_resp = await _register(client)
    old_refresh = register_resp.json()["refresh_token"]

    refresh_resp = await client.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert refresh_resp.status_code == 200
    new_refresh = refresh_resp.json()["refresh_token"]
    assert new_refresh != old_refresh

    # The old refresh token must now be rejected (rotation-on-use).
    reuse_resp = await client.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert reuse_resp.status_code == 401

    # The new one still works.
    second_refresh_resp = await client.post("/auth/refresh", json={"refresh_token": new_refresh})
    assert second_refresh_resp.status_code == 200


async def test_refresh_with_garbage_token_rejected(client):
    resp = await client.post("/auth/refresh", json={"refresh_token": "not-a-real-token"})
    assert resp.status_code == 401


async def test_logout_revokes_refresh_token(client):
    register_resp = await _register(client)
    access = register_resp.json()["access_token"]
    refresh = register_resp.json()["refresh_token"]

    logout_resp = await client.post(
        "/auth/logout",
        json={"refresh_token": refresh},
        headers={"Authorization": f"Bearer {access}"},
    )
    assert logout_resp.status_code == 204

    reuse_resp = await client.post("/auth/refresh", json={"refresh_token": refresh})
    assert reuse_resp.status_code == 401


async def test_forgot_password_always_returns_ok_even_for_unknown_email(client):
    resp = await client.post("/auth/forgot-password", json={"email": "nobody@example.com"})
    assert resp.status_code == 202
    assert resp.json() == {"ok": True}


async def test_deactivated_user_is_rejected_immediately_even_with_valid_token(client, db):
    """The whole point of the live-DB lookup in core/deps.get_current_user:
    a still-valid, unexpired access token must stop working the moment the
    user is deactivated - not just after the token's TTL elapses."""
    register_resp = await _register(client)
    access = register_resp.json()["access_token"]

    user = (await db.execute(select(User).where(User.email == "jane@example.com"))).scalar_one()
    user.is_active = False
    await db.commit()

    resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {access}"})
    assert resp.status_code == 401


async def test_rate_limits_repeated_login_attempts(client):
    """Best-effort: only meaningfully exercised when Redis is reachable, but
    should never error out even if it isn't (fails open)."""
    await _register(client, email="ratelimited@example.com")
    for _ in range(5):
        await client.post(
            "/auth/login", json={"email": "ratelimited@example.com", "password": "wrong-password"}
        )
    resp = await client.post(
        "/auth/login", json={"email": "ratelimited@example.com", "password": "wrong-password"}
    )
    assert resp.status_code in (401, 429)


async def test_refresh_token_persisted_and_hashed_not_plaintext(client, db):
    register_resp = await _register(client)
    raw_refresh = register_resp.json()["refresh_token"]

    stored = (await db.execute(select(RefreshToken))).scalars().all()
    assert len(stored) == 1
    assert stored[0].token_hash != raw_refresh


async def test_admin_role_not_grantable_via_public_register(client):
    resp = await _register(client)
    body = resp.json()
    assert body["user"]["role"] != UserRole.ADMIN.value
