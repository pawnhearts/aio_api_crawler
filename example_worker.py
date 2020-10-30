from example import Posts, Comments, Categories

from api_crawler.worker import Worker, SqliteSink, LoggingSink


class MyWorker(Worker):
    endpoint = Posts()
    sink = LoggingSink()

    async def process(self, obj):
        return {'id': obj['id', 'text': obj['text'].upper()]}


if __name__ == "__main__":
    MyWorker().run()
