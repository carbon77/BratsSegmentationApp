from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

from app.api.routes import router
from app.db.database import engine
from app.db.models import Base
from app.services.queue import start_queue_worker, stop_queue_worker

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    await start_queue_worker()
    try:
        yield
    finally:
        await stop_queue_worker()


app = FastAPI(lifespan=lifespan)
app.include_router(router)
