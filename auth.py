from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import User
from sqlalchemy.future import select
from schemas import UserResponse
from datetime import datetime, timedelta
from typing import Annotated
import os

SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key") # Replace with a strong, random key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: AsyncSession = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        bus_number: str = payload.get("sub")
        if bus_number is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).filter(User.bus_number == bus_number))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user

async def create_access_token(bus_number: str):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": bus_number, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def authenticate_user(db: AsyncSession, bus_number: str, password: str) -> User:
    result = await db.execute(select(User).filter(User.bus_number == bus_number))
    user = result.scalar_one_or_none()
    if not user:
        return None
    if not user.verify_password(password):
        return None
    return user