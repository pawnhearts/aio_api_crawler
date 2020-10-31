import asyncio

import sys
sys.path.append('..')

from api_crawler.endpoint import HtmlEndpoint
from api_crawler.sink import LoggingSink
from api_crawler.worker import Worker


class MotorDoc(HtmlEndpoint):
    url = "https://motor.readthedocs.io/en/stable/tutorial-asyncio.html"
    wrap_results = False

    class selector:
        selector = "div.body"
        many = False

        class h2s:
            selector = "h2 a:first-child"
            many = True
            type = "text"

        class links:
            selector = "h2 a:first-child"
            many = True
            type = "attr"
            attr = "href"


motordoc = MotorDoc()

worker = Worker(endpoint=motordoc, sinks=[LoggingSink()])

if __name__ == "__main__":
    worker.run()
