from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from core.config import settings


class DatabaseHelper:
    def __init__(self, url: str):
        self.engine = create_async_engine(
            url=url,
            echo=True,
        )
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    def get_session(self) -> AsyncSession:
        return self.session_factory()

    async def session_dependency(self) -> AsyncSession:
        async with self.session_factory() as sess:
            yield sess

    async def scoped_session_dependency(self) -> AsyncSession:
        async with self.session_factory() as sess:
            yield sess


db_helper = DatabaseHelper(
    url=settings.db_url,
)

