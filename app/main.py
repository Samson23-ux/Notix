import sentry_sdk
from fastapi import FastAPI
from contextlib import asynccontextmanager
from starlette.middleware.sessions import SessionMiddleware


from app.api.routers import router
from app.core.config import get_settings
from app.database.session import redis_client


settings = get_settings()


sentry_sdk.init(
    dsn=settings.SENTRY_SDK_DSN,
    enable_logs=True,
    send_default_pii=True,
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
    profile_lifecycle="trace",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = redis_client
    yield
    await app.state.redis.aclose()


app = FastAPI(
    lifespan=lifespan,
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
)


app.include_router(router.router)


app.add_middleware(
    SessionMiddleware,
    max_age=900,
    same_site="lax",
    secret_key=settings.SESSION_SECRET_KEY,
    https_only=settings.ENVIRONMENT == "production",
)


@app.get("/", status_code=200)
async def home():
    message: dict = {
        "status": "success",
        "message": "Welcome to Notix",
    }
    return message
