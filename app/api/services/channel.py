import pika
import aio_pika


from app.core.config import get_settings


class EventChannel:
    def __init__(self, broker_url: str):
        self._broker_url = broker_url
        self._sync_connection = None
        self._async_connection = None

    SETTINGS = get_settings()

    @property
    def sync_connection(self):
        return self._sync_connection

    def connect_sync(self):
        connection: pika.BlockingConnection = pika.BlockingConnection(
            pika.ConnectionParameters(self.SETTINGS.BROKER_HOST)
        )
        self._sync_connection = connection

    def close(self):
        self._sync_connection.close()

    async def aclose(self):
        await self._async_connection.close()

    async def connect_async(self):
        connection: aio_pika.RobustConnection = await aio_pika.connect_robust(
            self._broker_url
        )
        self._async_connection = connection

    async def create_exchange(self, name: str, **kwargs) -> aio_pika.Exchange:
        channel: aio_pika.Channel = await self._async_connection.channel()

        exchange: aio_pika.Exchange = await channel.declare_exchange(
            name, aio_pika.ExchangeType.DIRECT, **kwargs
        )
        return exchange

    async def create_queue(self, name: str, **kwargs) -> aio_pika.Queue:
        channel: aio_pika.Channel = await self._async_connection.channel()

        queue: aio_pika.Queue = await channel.declare_queue(name, **kwargs)
        return queue

    async def bind_queue(
        self, exchange: aio_pika.Exchange, name: str, routing_key: str, **kwargs
    ):
        queue: aio_pika.Queue = await self.create_queue(name, **kwargs)

        await queue.bind(exchange, routing_key=routing_key)

    async def queue_depth(self, name: str, **kwargs) -> int:
        channel: aio_pika.Channel = await self._async_connection.channel()
        queue: aio_pika.Queue = await channel.declare_queue(name, **kwargs)

        depth: int = await queue.declaration_result.message_count
        return depth
