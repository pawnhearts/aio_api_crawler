from typing import List
import importlib

from .base import Sink


class TortoiseSink(Sink):
    models_module: str
    db_url: str
    model_name: str

    async def init(self):
        from tortoise import Tortoise

        await Tortoise.init(
            db_url=self.db_url, modules={"models": [self.models_module]}
        )
        self.model = getattr(
            importlib.import_module(self.models_module), self.model_name
        )

    async def process(self, obj):
        orm_obj = self.model(**obj)
        await orm_obj.save()
        return True
