import sentry_sdk
from fastapi import FastAPI
from httpx import AsyncClient
from contextlib import asynccontextmanager
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler
from starlette.middleware.sessions import SessionMiddleware


from app.api.routers import router
from app.core.config import get_settings
from app.database.session import redis_client
from app.api.services.channel import EventChannel

SETTINGS = get_settings()


sentry_sdk.init(
    dsn=SETTINGS.SENTRY_SDK_DSN,
    enable_logs=True,
    send_default_pii=True,
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
    profile_lifecycle="trace",
)


async def create_exchange_and_queue(channel: EventChannel):
    dlqs = SETTINGS.BROKER_DLQ
    queues = SETTINGS.BROKER_QUEUE

    dlq_exchange = await channel.create_exchange("notix.dlx", durable=True)
    queue_exchange = await channel.create_exchange("notix.direct", durable=True)

    for n, rk in dlqs:
        await channel.bind_queue(dlq_exchange, n, rk, durable=True)

    for n, rk in queues:
        await channel.bind_queue(
            queue_exchange,
            n,
            rk,
            durable=True,
            x_max_priority=10,
            x_dead_letter_exchange="notix.dlx",
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = redis_client
    app.state.client = AsyncClient(base_url="http://localhost/api/v1", timeout=10.0)

    event_channel = EventChannel(SETTINGS.BROKER_URL)
    await create_exchange_and_queue(event_channel)

    yield

    await app.state.redis.aclose()
    await app.state.client.aclose()
    await event_channel.aclose()


app = FastAPI(
    lifespan=lifespan,
    title=SETTINGS.API_TITLE,
    version=SETTINGS.API_VERSION,
    description=SETTINGS.API_DESCRIPTION,
)


app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


app.include_router(router.router)


app.add_middleware(
    SessionMiddleware,
    max_age=900,
    same_site="lax",
    secret_key=SETTINGS.SESSION_SECRET_KEY,
    https_only=SETTINGS.ENVIRONMENT == "production",
)


@app.get("/", status_code=200)
async def home():
    message: dict = {
        "status": "success",
        "message": "Welcome to Notix",
    }
    return message
