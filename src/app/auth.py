from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app import security

bearer_scheme = HTTPBearer()
AUTH_REQUIRED_MESSAGE = "Authentication required"

def require_token_type(token_type: str):
    async def dependency(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> int:
        token = credentials.credentials
        try:
            payload = security.decode_token(token=token)
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail=AUTH_REQUIRED_MESSAGE)
        if payload.get("type") != token_type:
            raise HTTPException(status_code=401, detail=AUTH_REQUIRED_MESSAGE)
        return int(payload["sub"])
    return dependency

get_current_user_id = require_token_type("access")
get_refresh_user_id = require_token_type("refresh")
CurrentUserDependency = Annotated[int, Depends(get_current_user_id)]
RefreshUserDependency = Annotated[int, Depends(get_refresh_user_id)]