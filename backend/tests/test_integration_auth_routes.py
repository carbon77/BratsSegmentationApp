from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import router
from app.db.models import User


def test_register_then_login_happy_path():
    test_app = FastAPI()
    test_app.include_router(router)

    users = {}

    class FakeQuery:
        def __init__(self):
            self.email = None

        def filter(self, *criteria):
            for expr in criteria:
                right = getattr(expr, "right", None)
                if right is not None and hasattr(right, "value"):
                    self.email = right.value
            return self

        def first(self):
            return users.get(self.email)

    class FakeDB:
        next_id = 1

        def __init__(self):
            self._pending = None

        def query(self, _model):
            return FakeQuery()

        def add(self, user):
            self._pending = user

        def commit(self):
            if self._pending is not None:
                self._pending.id = FakeDB.next_id
                FakeDB.next_id += 1
                users[self._pending.email] = self._pending
                self._pending = None

        def refresh(self, _user):
            return None

    db = FakeDB()

    from app.db.database import get_db

    def fake_get_db():
        yield db

    test_app.dependency_overrides[get_db] = fake_get_db

    with TestClient(test_app) as client:
        register_response = client.post(
            "/auth/register",
            json={"name": "Alice", "email": "alice@example.com", "password": "secret"},
        )
        assert register_response.status_code == 201

        login_response = client.post(
            "/auth/login",
            json={"email": "alice@example.com", "password": "secret"},
        )
        assert login_response.status_code == 200

        payload = login_response.json()
        assert payload["token_type"] == "bearer"
        assert payload["user"]["email"] == "alice@example.com"
        assert payload["access_token"]
