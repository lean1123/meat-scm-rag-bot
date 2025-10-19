import os
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.services.user_service import get_user_service, UserService

# NOTE: when used as dependency, FastAPI will inject UserService via Depends(get_user_service)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 24

security = HTTPBearer()


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_MINUTES)
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


async def get_current_user(credentials=Depends(security), user_service: UserService = Depends(get_user_service)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        email: str = payload.get("email")
        farm_id: str = payload.get("facilityID")
        if email is None or farm_id is None:
            raise credentials_exception
        token_data = TokenData(username=email)
    except JWTError:
        raise credentials_exception

    # Tìm user trong DB bằng UserService
    user_data = user_service.get_user_by_email(email=token_data.username, farm_id=farm_id)
    if user_data is None:
        raise credentials_exception

    # Trả về Pydantic User
    try:
        user = User(**user_data)
    except Exception:
        # đảm bảo trường hợp dữ liệu DB không đầy đủ sẽ bị coi là unauthorized
        raise credentials_exception

    return user
