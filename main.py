from fastapi import FastAPI
from contextlib import asynccontextmanager
from arq import create_pool
from arq.connections import RedisSettings
from routers import user, client , business, job , service , quotation , invoice, Marketplace

@asynccontextmanager
async def lifespan(app:FastAPI):
    app.state.arq= await create_pool(RedisSettings())
    yield
    await app.state.arq.close()



app=FastAPI(lifespan=lifespan)
app.include_router(user.router)
app.include_router(client.router)
app.include_router(business.router)
app.include_router(job.router)
app.include_router(service.router)
app.include_router(quotation.router)
app.include_router(invoice.router)
app.include_router(Marketplace.router)