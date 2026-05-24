from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import router


def test_scans_endpoint_handles_parallel_requests():
    test_app = FastAPI()
    test_app.include_router(router)

    class DummyUser:
        id = 42

    class FakeQuery:
        def filter(self, *_args, **_kwargs):
            return self

        def order_by(self, *_args, **_kwargs):
            return self

        def all(self):
            return []

    class FakeDB:
        def query(self, _model):
            return FakeQuery()

    from app.api.routes import get_current_user
    from app.db.database import get_db

    async def fake_current_user():
        return DummyUser()

    def fake_get_db():
        yield FakeDB()

    test_app.dependency_overrides[get_current_user] = fake_current_user
    test_app.dependency_overrides[get_db] = fake_get_db

    with TestClient(test_app) as client:
        def call_scans():
            return client.get("/scans").status_code

        with ThreadPoolExecutor(max_workers=12) as pool:
            statuses = list(pool.map(lambda _i: call_scans(), range(30)))

    assert all(status == 200 for status in statuses)
