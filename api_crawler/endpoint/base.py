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


class ResultWrapper:
    def __init__(self, data, url, params):
        self.data = data
        self.url = url
        self.params = params

    def __getattr__(self, item):
        return getattr(self.data, item)

    def __getitem__(self, item):
        return self.data[item]

    def __repr__(self):
        return repr(self.data)

    def __str__(self):
        return str(self.data)

    def __iter__(self):
        return iter(self.data)


def ResultWrapper(data, url, params):
    return type("ResultWrapper", (data.__class__,), {"params": params, "url": url})(data)


def UrlWrapper(s, params):
    class UrlWrapper(str):
        params = None

    obj = UrlWrapper(s)
    obj.params = params
    return obj


class Endpoint:
    url: str = ""
    params: Dict[
        str, Union[int, str, Iterable, AsyncGenerator, Awaitable, Callable]
    ] = {}
    params_type = "params"
    url_params: Dict[
        str, Union[int, str, Iterable, AsyncGenerator, Awaitable, Callable]
    ] = {}
    method = "get"
    good_statuses: List[int] = [200]
    headers: Dict[
        str, Union[int, str, Iterable, AsyncGenerator, Awaitable, Callable]
    ] = {}
    cookies: Dict[
        str, Union[int, str, Iterable, AsyncGenerator, Awaitable, Callable]
    ] = {}
    proxy: Optional[Union[str, Callable, Awaitable, Iterable, AsyncGenerator]] = None

    def __init__(self, session=None, **kwargs):
        self.session = session or aiohttp.ClientSession()
        for key, value in kwargs.items():
            if not hasattr(self, key):
                raise AttributeError(f"{self} has no attribute {key}")
            if isinstance(getattr(self, key), dict):
                setattr(self, key, dict(getattr(self, key)))
                getattr(self, key).update(value)
            else:
                setattr(self, key, value)
        if self.params_type not in ["params", "data", "json"]:
            raise AttributeError(f'params_type should be "params", "data" or "json"')

    async def perform_request(self, url, **kwargs):
        async with self.session.request(self.method, url, **kwargs) as res:
            if res.status in self.good_statuses:
                return await self.fetch(res)
            else:
                log.exception(f'Request status for {url}: {res.status}')

    async def fetch(self, response):
        return await response.text()

    async def _call_callables(self, params):
        if any(callable(value) for value in params.values()):
            return {
                key: await value if awaitable(value) else value
                for key, value in [
                    (key, (value() if callable(value) else value))
                    for key, value in params.items()
                ]
            }
        return params

    async def iter_params(self, params=None):
        if params is None:
            params = self.params
        for key, value in params.items():
            if iterable(value) and not isinstance(value, range):
                for i in value:
                    yield self.iter_params(copydict(params, key, i))
                return
            elif async_iterable(value):
                async for i in value:
                    yield self.iter_params(copydict(params, key, i))
                return
        ranges = [
            (key, value) for key, value in params.items() if isinstance(value, range)
        ]
        for key, value in ranges:
            for i in value:
                new_params = dict(params)
                new_params[key] = i
                if len(ranges) == 1:
                    async for res in self.iter_params(new_params):
                        yield res
                else:
                    yield self.iter_params(new_params)
            return
        yield await self._call_callables(params)

    async def iter_urls(self, url_params=None):
        if url_params is None:
            url_params = self.iter_params(self.url_params)
        async for params in url_params:
            if isinstance(params, dict):
                params = await self._call_callables(params)
                yield UrlWrapper(self.url.format(**params), params)
            else:
                yield self.iter_urls(params)

    async def get_proxy(self):
        if iterable(self.proxy):
            return next(self.proxy)
        elif async_iterable(self.proxy):
            return self.proxy.__anext__()
        elif callable(self.proxy):
            res = self.proxy()
            if awaitable(res):
                return await res
            else:
                return res
        else:
            return self.proxy

    def transform(self, results):
        return results

    async def get_results(self, url, params):
        args = {
            self.params_type: params,
            "headers": await self._call_callables(self.headers),
            "cookies": await self._call_callables(self.cookies),
            "proxy": await self.get_proxy(),
        }
        res = await self.perform_request(url, **args)
        return self.transform(res)

    async def _iter_url(self, url):
        yield url

    async def iter_results(self, iurls=None, iparams=None, wrap_results=True):
        if iurls is None:
            iurls = self.iter_urls()
        if iparams is None:
            iparams = self.iter_params()
        async for url in iurls:
            if isinstance(url, str):
                async for params in iparams:
                    if isinstance(params, dict):
                        results = await self.get_results(url, params)
                        if iterable(results):
                            for res in results:
                                yield ResultWrapper(
                                    res, url, params
                                ) if wrap_results else res
                        elif results:
                            yield ResultWrapper(
                                results, url, params
                            ) if wrap_results else results
                        else:
                            return
                    else:
                        async for res in self.iter_results(self._iter_url(url), params):
                            yield res
            else:
                async for res in self.iter_results(url):
                    yield res

    async def results(self):
        return [res async for res in self.iter_results()]

    def __aiter__(self):
        return self.iter_results()
