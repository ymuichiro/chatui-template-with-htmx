from datetime import datetime, timedelta, timezone

import jwt

secret = "dev-secret-change-me"
now = datetime.now(timezone.utc)
payload = {
    "sub": "demo-user",
    "name": "Demo User",
    "email": "demo@example.com",
    "iss": "chatui-dev",
    "aud": "chatui",
    "iat": int(now.timestamp()),
    "exp": int((now + timedelta(hours=8)).timestamp()),
}
print(jwt.encode(payload, secret, algorithm="HS256"))
