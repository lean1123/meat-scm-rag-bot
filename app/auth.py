from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
from app.services.user_service import get_user_by_username
import os

SECRET_KEY = os.getenv("SECRET_KEY", "a_very_secret_key_for_dev")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


class User(BaseModel):
    id: str
    email: str
    name: str
    role: str
    facilityID: str
    status: str
    fabricEnrollmentID: str
    is_active: bool = True


class TokenData(BaseModel):
    username: str | None = None


async def get_current_user(credentials=Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        farm_id: str = payload.get("facilityID")
        if username is None or farm_id is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    # Kiểm tra user có tồn tại trong database không
    user_data = get_user_by_username(token_data.username, farm_id)
    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found in database",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Kiểm tra user có đang active không
    if not user_data.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = User(**user_data)
    return user