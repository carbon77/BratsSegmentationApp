import pytest

from app.dto.dto import RegisterRequest
from app.services.auth import hash_password, verify_password


def test_hash_and_verify_password_roundtrip():
    password = "SuperSecret123!"

    password_hash = hash_password(password)

    assert password_hash.startswith("pbkdf2_sha256$")
    assert verify_password(password, password_hash)
    assert not verify_password("wrong-password", password_hash)


def test_register_request_normalizes_email_and_name():
    payload = RegisterRequest(name="  Alice Doe  ", email="  ALICE@EXAMPLE.COM  ", password="pass")

    assert payload.name == "Alice Doe"
    assert payload.email == "alice@example.com"


@pytest.mark.parametrize("email", ["", "not-an-email", "missing-at.domain"])
def test_register_request_rejects_invalid_email(email):
    with pytest.raises(ValueError):
        RegisterRequest(name="Alice", email=email, password="pass")
