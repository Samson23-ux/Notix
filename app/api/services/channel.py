import pika
import aio_pika


from app.core.config import get_settings


class EventChannel:
    def __init__(self, broker_url: str):
        self._broker_url = broker_url
        self._sync_connection = None
        self._async_connection = None

    SETTINGS = get_settings()

    async def connect_async(self):
        connection: aio_pika.RobustConnection = await aio_pika.connect_robust(
            self._broker_url
        )
        self._async_connection = connection

    async def aclose(self):
        await self._async_connection.close()

    async def create_exchange(
        self,
        name: str,
        durable: bool = True,
    ) -> aio_pika.Exchange:
        channel: aio_pika.Channel = await self._async_connection.channel()

        exchange: aio_pika.Exchange = await channel.declare_exchange(
            name, aio_pika.ExchangeType.DIRECT, durable=durable
        )
        return exchange

    async def create_queue(
        self, name: str, durable: bool = True, arguments: dict = None
    ) -> aio_pika.Queue:
        channel: aio_pika.Channel = await self._async_connection.channel()

        queue: aio_pika.Queue = await channel.declare_queue(
            name, durable=durable, arguments=arguments
        )
        return queue

    async def bind_queue(
        self,
        exchange: aio_pika.Exchange,
        name: str,
        routing_key: str,
        durable: bool = True,
        arguments: dict = None,
    ):
        queue: aio_pika.Queue = await self.create_queue(
            name, durable=durable, arguments=arguments
        )

        await queue.bind(exchange, routing_key=routing_key)

    async def queue_depth(self, name: str, passive: bool = True) -> int:
        channel: aio_pika.Channel = await self._async_connection.channel()
        queue: aio_pika.Queue = await channel.declare_queue(name, passive=passive)

        depth: int = queue.declaration_result.message_count
        return depth

    def connect_sync(self):
        connection: pika.BlockingConnection = pika.BlockingConnection(
            pika.URLParameters(self.SETTINGS.BROKER_URL)
        )
        self._sync_connection = connection

    def close(self):
        self._sync_connection.close()

    def sync_queue_depth(self, name: str, passive: bool = True) -> int:
        channel: pika.BlockingConnection = self._sync_connection.channel()
        queue: pika.BlockingConnection = channel.queue_declare(name, passive=passive)

        depth: int = queue.method.message_count
        return depth
