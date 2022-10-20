from typing import List

from fastapi import APIRouter

router = APIRouter(prefix="/kelvin", tags=["kelvin"])


@router.get("/examples/list", response_model=List[str])
async def list():
    return ["example 1", "example 2", "example 3"]
