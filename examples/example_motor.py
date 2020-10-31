from example import Posts


from api_crawler.worker import Worker
from api_crawler.sink import MotorSink


class MyWorker(Worker):
    endpoint = Posts()
    sinks = [MotorSink(db_url='mongodb://root:example@localhost/', db_name='test', collection_name='test')]


if __name__ == "__main__":
    MyWorker().run()
