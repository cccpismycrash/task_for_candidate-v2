from sqlalchemy import Float, String, BigInteger
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine, AsyncSession
import asyncio
from config_reader import config

engine = create_async_engine(url=config.DATABASE_URL, echo=True)

# postgresql+asyncpg://postgres:qwerty47@localhost/notdb

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata)
        await conn.run_sync(Base.metadata.create_all)


async def add_column(act_time: str, text: str, value: float):
    async with async_session.begin() as session:
        new_row = Notification(time=act_time, post_text=text,value_share=value)
        session.add(new_row)
        await session.commit()


class Base(AsyncAttrs, DeclarativeBase):
    pass

class Notification(Base):
    __tablename__ = 'notifications'
    
    id = mapped_column(BigInteger, primary_key=True, index=True, unique=True)
    time = mapped_column(String)
    post_text = mapped_column(String)
    value_share = mapped_column(Float)

async def init_models():
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

if __name__ == '__main__':
    asyncio.run(init_models())
