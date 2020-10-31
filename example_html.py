from api_crawler.endpoint import HtmlEndpoint
from api_crawler.sink import LoggingSink
from api_crawler.worker import Worker


class MotorDoc(HtmlEndpoint):
    url = 'https://motor.readthedocs.io/en/stable/tutorial-asyncio.html'
    selector = 'div.body div.section'
    select_one = False
    select_type = 'text'


worker = Worker(endpoint=MotorDoc(), sinks=[LoggingSink()])
worker.run()
