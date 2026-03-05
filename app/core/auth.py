from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, Header, HTTPException, status

from app.core.config import settings
from app.schemas.auth import CurrentUser


def _decode_jwt(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired JWT",
        ) from exc


def _extract_bearer(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    if not authorization.lower().startswith("bearer "):
        return None
    return authorization.split(" ", 1)[1].strip() or None


def _build_dev_demo_claims() -> dict:
    now = datetime.now(timezone.utc)
    return {
        "sub": settings.dev_demo_user_id,
        "name": settings.dev_demo_user_name,
        "email": settings.dev_demo_user_email,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=8)).timestamp()),
        "dummy_auth": True,
    }


def get_current_user(
    authorization: Optional[str] = Header(default=None),
    x_forwarded_jwt: Optional[str] = Header(default=None),
) -> CurrentUser:
    if settings.auth_mode not in {"proxy", "dev_demo"}:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid AUTH_MODE. expected: proxy | dev_demo",
        )

    if settings.auth_mode == "proxy":
        token = x_forwarded_jwt
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing forwarded JWT header",
            )
    else:
        token = x_forwarded_jwt or _extract_bearer(authorization)
        if not token:
            if settings.dev_demo_auto_auth_without_jwt:
                claims = _build_dev_demo_claims()
                return CurrentUser(
                    user_id=settings.dev_demo_user_id,
                    claims=claims,
                    auth_mode=settings.auth_mode,
                )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing JWT header",
            )

    claims = _decode_jwt(token)
    sub = claims.get("sub")
    if not isinstance(sub, str) or not sub.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing sub claim",
        )

    return CurrentUser(user_id=sub, claims=claims, auth_mode=settings.auth_mode)


CurrentUserDep = Depends(get_current_user)
