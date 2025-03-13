import uvicorn

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from shared.core.models.db_helper import db_helper
from .gen_router import router as general_router
from user.views import router as user_router
from auth.jwt_auth import router as auth_router
from shared.clients.redis.RedisClient import init_redis, close_redis
from shared.clients.kafka.async_kafka_producer import async_kafka_producer

from shared.core.models.base import Base

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with db_helper.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    await init_redis()
    
    async_kafka_producer.start()
    
    yield
    
    await close_redis()
    
    await async_kafka_producer.stop()


app = FastAPI(lifespan = lifespan)


app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(general_router)
app.include_router(auth_router)
app.include_router(user_router)


origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://0.0.0.0:5173",
    "http://127.0.0.1:8000",
    "http://0.0.0.0:8000",
    'http://localhost:8000',
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


if __name__ == '__main__':
    uvicorn.run('run:app', host="localhost", port=8000, reload=True)
