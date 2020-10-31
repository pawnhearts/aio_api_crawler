from .base import Sink


class MotorSink(Sink):
    db_url: str
    db_name: str
    collection_name: str

    def transform(self, obj):
        return repr(obj)

    async def init(self):
        import motor.motor_asyncio
        self.client = motor.motor_asyncio.AsyncIOMotorClient(self.db_url)
        self.collection = self.client[self.db_name][self.collection_name]

    async def process(self, obj):
        result = await self.collection.insert_one(obj)
        return result.inserted_id
