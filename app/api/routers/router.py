from fastapi import APIRouter


from app.core.config import get_settings


router = APIRouter(prefix=get_settings().API_PREFIX)
