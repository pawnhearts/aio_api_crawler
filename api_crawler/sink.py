import asyncio


class Sink:
    def __init__(self, num_tasks=1, **kwargs):
        self.num_tasks = num_tasks
        self.queue = asyncio.Queue()
        self.tasks = []
        for k, v in kwargs.items():
            setattr(self, k, v)

    async def init(self):
        pass

    async def __aenter__(self):
        await self.init()
        self.tasks = [asyncio.create_task(self.run()) for _ in range(self.num_tasks)]
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.queue.join()
        for task in self.tasks:
            task.cancel()

    async def run(self):
        while True:
            obj = await self.queue.get()
            new_obj = self.transform(obj)
            if new_obj is not None:
                await self.process(new_obj)
            self.queue.task_done()

    async def put(self, obj):
        await self.queue.put(obj)

    def transform(self, obj):
        return obj

    async def process(self, obj):
        pass


class LoggingSink(Sink):
    def transform(self, obj):
        return repr(obj)

    async def init(self):
        from loguru import logger

        self.logger = logger

    async def process(self, obj):
        self.logger.info(obj)
        return True
