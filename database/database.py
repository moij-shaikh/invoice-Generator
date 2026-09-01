from sqlalchemy.ext.asyncio import create_async_engine  , async_sessionmaker

from config import DATABASE_URL

engine=create_async_engine(DATABASE_URL)

async_local_session=async_sessionmaker(bind=engine,autoflush=True , expire_on_commit=False)

async def get_db():
    async with async_local_session() as db:
        yield db
