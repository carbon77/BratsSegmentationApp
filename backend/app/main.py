from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

from app.api.routes import router
from app.db.database import engine
from app.db.models import Base
from app.services.inference import preload_model
from app.services.schema import ensure_schema
from app.services.tasks import start_task_producer, stop_task_producer

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    ensure_schema(engine)
    preload_model()
    await start_task_producer()
    yield
    await stop_task_producer()


app = FastAPI(lifespan=lifespan)
app.include_router(router)
