from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import ssl
from config  import DATABASE_URL
# The base URL without any ssl parameters in the query string



engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    
)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def init_db():
    print("Initializing database...")
    try:
        async with engine.begin() as conn:
            print(f"conn is {conn}")
            await conn.run_sync(Base.metadata.create_all)
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Database initialization failed: {e}")

