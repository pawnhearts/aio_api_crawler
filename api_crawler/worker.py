import asyncio
from typing import List

import aiohttp
from aiohttp import TCPConnector

from api_crawler import JsonEndpoint


class Sink:
    async def put(self, obj):
        return True


class LoggingSink(Sink):
    def __init__(self):
        from loguru import logger

        self.log = logger

    async def init(self):
        pass

    async def put(self, obj):
        self.log.info(obj)
        return True


class SqliteSink(Sink):
    """ For demo purposes only """

    pk: str = "id"
    table: str = "table"
    columns: List[str] = ["id"]

    def get_pk(self, obj):
        return obj[self.pk]

    def __init__(self, db):
        self.db = db

    async def init(self):
        from aiosqlite import connect

        self.conn = await connect(self.db)
        try:
            async with self.conn.cursor() as cur:
                await cur.execute(
                    f'CREATE TABLE {self.table}({",".join(self.columns)});'
                )
        except Exception as e:
            print(e)

    async def put(self, obj):
        async with self.conn.cursor() as cur:
            pk = self.get_pk(obj)
            cursor = await cur.execute(
                f"SELECT {self.pk} FROM {self.table} WHERE {self.pk}=?", (pk,)
            )
            if await cursor.fetchone():
                return False
            await cur.execute(
                f'INSERT INTO {self.table}({",".join(self.columns)}) VALUES({",".join("?" for _ in self.columns)})',
                tuple(obj[col] for col in self.columns),
            )
            return True


class Worker:
    endpoint: JsonEndpoint
    sink: Sink

    def run(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.pipeline())

    async def transform(self, obj):
        return obj

    async def pipeline(self):
        await self.sink.init()
        async for obj in self.endpoint.iter_results():
            new_obj = await self.transform(obj)
            if not (await self.sink.put(new_obj)):
                break
