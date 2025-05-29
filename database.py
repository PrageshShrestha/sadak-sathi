<<<<<<< HEAD
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
=======
# database.py
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from base import Base  # Import Base from base.py

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:helloworld@localhost/uvicorn2")

engine = create_async_engine(DATABASE_URL, echo=True)

# Asynchronous session maker
async_session_maker = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

# Utility function to get DB session
async def get_db():
    async with async_session_maker() as session:
        yield session
>>>>>>> 818a14e1226f981c3d9864e53ac84e04fd6561e1
