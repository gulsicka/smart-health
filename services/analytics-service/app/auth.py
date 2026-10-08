from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel

from app.config import settings
from app.enums import RoleName

bearer_scheme = HTTPBearer()


class TokenData(BaseModel):
    user_id: int
    roles: list[RoleName]


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
        return TokenData(user_id=user_id, roles=payload.get("roles", []))
    except JWTError:
        raise credentials_exception


def require_role(*roles: RoleName):
    def dependency(current_user: TokenData = Depends(get_current_user)):
        if not any(r in roles for r in current_user.roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to perform this action",
            )
        return current_user
    return dependency
