from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from core.config import settings

engine = create_async_engine(
    url=settings.db.url,
    echo=settings.db.echo,
    echo_pool=settings.db.echo_pool,
    connect_args=settings.db.connect_args,
)

async_session_fabric = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


async def get_session():
    async with async_session_fabric() as sess:
        try:
            yield sess
        except Exception:
            await sess.rollback()
            raise
