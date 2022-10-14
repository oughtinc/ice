from fastapi import Depends
from fastapi import HTTPException
from fastapi.security import APIKeyHeader

from ice.settings import settings


# TODO: Replace this with per-user auth so we can attribute API usage.
def check_auth(key: str = Depends(APIKeyHeader(name="X-Api-Key"))):
    expected_key = settings.NEXT_PUBLIC_BACKEND_API_KEY
    if expected_key and key != expected_key:
        raise HTTPException(status_code=403, detail="Invalid API Key")
