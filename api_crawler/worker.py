import asyncio
from contextlib import AsyncExitStack
from typing import List, Dict

from aiohttp import ClientSession

from api_crawler import JsonEndpoint
from api_crawler.sink import Sink


class Worker:
    endpoint: JsonEndpoint
    sinks: List[Sink]

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def run(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.pipeline())

    def transform(self, obj):
        return obj

    async def pipeline(self):
        async with AsyncExitStack() as stack:
            sinks = [await stack.enter_async_context(sink) for sink in self.sinks]
            async with ClientSession() as session:
                self.endpoint.session = session
                async for obj in self.endpoint.iter_results():
                    new_obj = self.transform(obj)
                    if new_obj:
                        for sink in sinks:
                            await sink.put(new_obj)


class WorkerGroup:
    map: Dict[JsonEndpoint, List[Sink]] = {}
    workers: List[Worker] = []

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        for endpoint, sinks in self.map.items():
            self.workers.append(Worker(endpoint=endpoint, sinks=sinks))

    def run(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            asyncio.gather(*[worker.pipeline() for worker in self.workers])
        )
