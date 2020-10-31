from .base import Sink


class LoggingSink(Sink):
    def transform(self, obj):
        return repr(obj)

    async def init(self):
        from loguru import logger

        self.logger = logger

    async def process(self, obj):
        self.logger.info(obj)
        return True
