from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..domain import Base


class DatabaseHelper:
    def __init__(self, db_url: str, async_mode: bool = True):
        self.async_mode = async_mode
        if async_mode:
            self._engine = create_async_engine(url=db_url)
            self.session_maker = async_sessionmaker(
                bind=self._engine,
                autoflush=False,
                expire_on_commit=False,
                autocommit=False
            )
        else:
            self._engine = create_engine(url=db_url)
            self.session_maker = sessionmaker(
                bind=self._engine,
                autoflush=False,
                expire_on_commit=False,
                autocommit=False
            )

    async def session_dependency(self):
        session = self.session_maker()
        try:
            yield session
        finally:
            if self.async_mode:
                await session.close()
            else:
                session.close()

    async def create_schema(self):
        if self.async_mode:
            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        else:
            Base.metadata.create_all(self._engine)

    async def del_schema(self):
        if self.async_mode:
            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
        else:
            Base.metadata.drop_all(self._engine)
