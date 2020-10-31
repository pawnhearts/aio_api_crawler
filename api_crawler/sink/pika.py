import json

from .base import Sink


class PikaSink(Sink):
    amqp_url: str
    routing_key: str

    async def init(self):
        import aio_pika

        self.connection = await aio_pika.connect_robust(self.amqp_url)
        self.channel = await self.connection.channel()

    async def process(self, obj):
        import aio_pika

        await self.channel.default_exchange.publish(
            aio_pika.Message(body=json.dumps(obj)), routing_key=self.routing_key
        )
        return True

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.connection.close()
        super().__aexit__()
