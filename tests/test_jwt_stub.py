from datetime import datetime, timedelta, timezone

import jwt
import pytest


def test_decode_accepts_single_algorithm_string():
    payload = {"sub": "user", "exp": 9999999999}
    token = jwt.encode(payload, "secret", algorithm="HS256")

    decoded = jwt.decode(token, "secret", algorithms="HS256")

    assert decoded == payload


def test_decode_enforces_required_claims():
    token = jwt.encode({"sub": "user"}, "secret", algorithm="HS256")

    with pytest.raises(jwt.MissingRequiredClaimError):
        jwt.decode(
            token,
            "secret",
            algorithms=["HS256"],
            options={"require": ["exp"]},
        )


def test_decode_respects_not_before_claim():
    future = datetime.now(timezone.utc) + timedelta(seconds=60)
    payload = {"sub": "user", "nbf": future, "exp": future + timedelta(seconds=60)}
    token = jwt.encode(payload, "secret", algorithm="HS256")

    with pytest.raises(jwt.ImmatureSignatureError):
        jwt.decode(token, "secret", algorithms=["HS256"])


def test_decode_not_before_allows_leeway():
    future = datetime.now(timezone.utc) + timedelta(seconds=30)
    payload = {"sub": "user", "nbf": future, "exp": future + timedelta(seconds=60)}
    token = jwt.encode(payload, "secret", algorithm="HS256")

    decoded = jwt.decode(token, "secret", algorithms=["HS256"], leeway=45)

    assert decoded["nbf"] == int(future.timestamp())


def test_decode_accepts_timedelta_leeway():
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "user",
        "exp": now - timedelta(seconds=30),
        "nbf": now + timedelta(seconds=30),
        "iat": now + timedelta(seconds=30),
    }
    token = jwt.encode(payload, "secret", algorithm="HS256")

    decoded = jwt.decode(token, "secret", algorithms=["HS256"], leeway=timedelta(seconds=45))

    assert decoded["exp"] == int(payload["exp"].timestamp())


def test_decode_validates_audience():
    payload = {"sub": "user", "aud": "expected", "exp": 9999999999}
    token = jwt.encode(payload, "secret", algorithm="HS256")

    decoded = jwt.decode(token, "secret", algorithms=["HS256"], audience="expected")
    assert decoded["aud"] == "expected"

    with pytest.raises(jwt.InvalidAudienceError):
        jwt.decode(token, "secret", algorithms=["HS256"], audience="other")


def test_exceptions_module_matches_top_level_exports():
    from jwt import exceptions as exc

    assert exc.InvalidTokenError is jwt.InvalidTokenError
    assert exc.ExpiredSignatureError is jwt.ExpiredSignatureError
    assert exc.ImmatureSignatureError is jwt.ImmatureSignatureError
