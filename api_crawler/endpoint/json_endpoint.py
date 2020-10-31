from json import JSONDecodeError
from typing import (
    Optional,
    Iterable,
    Callable,
    AsyncGenerator,
    Awaitable,
    Dict,
    Union,
    List,
)
import aiohttp
from aiohttp import TCPConnector, ContentTypeError
from loguru import logger as log

from .base import Endpoint


def iterable(arg):
    return isinstance(arg, Iterable) and not isinstance(arg, str)


def async_iterable(arg):
    return isinstance(arg, AsyncGenerator)


def awaitable(arg):
    return isinstance(arg, Awaitable)


def copydict(d, key=None, value=None, **kwargs):
    res = dict(d)
    if key:
        res[key] = value
    res.update(kwargs)
    return res


class JsonEndpoint(Endpoint):
    results_key: Optional[
        str
    ] = None  # can be compound 'page.results' would grab data['page']['results']

    async def fetch(self, response):
        try:
            return await response.json(content_type=None)
        except (JSONDecodeError, ContentTypeError) as e:
            log.exception(e)
            return

    def _get_results_by_keys(self, res, keys):
        if not keys:
            return res
        if not isinstance(res, (list, dict)):
            raise ValueError(f"Keys are {keys} but result is not a list or dict")
        key = keys.pop(0)
        if key == "*":
            if not isinstance(res, list):
                raise ValueError("Key is * but result is not a list")
            return [self._get_results_by_keys(elem, list(keys)) for elem in res]
        else:
            return self._get_results_by_keys(res[key], list(keys))

    def transform(self, results):
        if results and self.results_key:
            try:
                return self._get_results_by_keys(results, self.results_key.split("."))
            except (IndexError, KeyError, ValueError) as e:
                log.exception(e)
                return
