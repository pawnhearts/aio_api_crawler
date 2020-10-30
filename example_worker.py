from example import Posts, Comments, Categories

from api_crawler.worker import Worker
from api_crawler.sink import LoggingSink


class MyWorker(Worker):
    endpoint = Posts()
    sinks = [LoggingSink()]

    def process(self, obj):
        return {'id': obj['id', 'text': obj['text'].upper()]}


if __name__ == "__main__":
    MyWorker().run()
