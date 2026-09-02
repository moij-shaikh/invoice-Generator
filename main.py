from fastapi import FastAPI
from contextlib import asynccontextmanager
from arq import create_pool
from arq.connections import RedisSettings
from routers import user

@asynccontextmanager
async def lifespan(app:FastAPI):
    app.state.arq_redis= create_pool(RedisSettings())
    yield
    await app.state.arq_redis.close()



app=FastAPI()
app.include_router(user.router)