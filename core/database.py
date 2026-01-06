from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from core.configs import settings

if not settings.DB_URL:
    raise ValueError("No valid database URL found. Check your configuration.")

db_url = (
    settings.DB_URL.replace("postgresql://", "postgresql+asyncpg://")
    if settings.DB_URL.startswith("postgresql://")  # type: ignore
    else settings.DB_URL
)

# Apply check_same_thread only for SQLite
connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}


engine = create_async_engine(url=db_url, connect_args=connect_args)
AsyncSessionLocal = async_sessionmaker(bind=engine,expire_on_commit=False)
Base = declarative_base()


async def get_db():
    db = AsyncSessionLocal()
    try:
        yield db
    except Exception:
        await db.rollback()
        raise
    finally:
        await db.close()
