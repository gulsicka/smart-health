from datetime import datetime, timedelta
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from . import schemas
from .config import settings
from .enums import RoleName
from .redis import get_redis

bearer_scheme = HTTPBearer()


def create_access_token(data: schemas.TokenPayload):
    to_encode = data.model_dump()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "jti": str(uuid.uuid4())})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), redis = Depends(get_redis),):
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        is_token_invalid = await redis.get(f"blacklist:{payload.get('jti')}")
        if is_token_invalid:
            raise credentials_exception
        user_id: int = payload.get("user_id")
        roles: list = payload.get("roles", [])
        if user_id is None:
            raise credentials_exception
        return schemas.TokenData(user_id=user_id, roles=roles)
    except JWTError:
        raise credentials_exception


def require_role(*roles: RoleName):
    def dependency(current_user: schemas.TokenData = Depends(get_current_user)):
        if not any(r in roles for r in current_user.roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to perform this action",
            )
        return current_user
    return dependency

def get_jti_from_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        jti: str = payload.get("jti")
        if jti is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token does not contain a jti claim",
            )
        return jti
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )