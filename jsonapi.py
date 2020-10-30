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
from urllib import parse


# class Paginator:
#     next_page: Optional[str] = None
#     pages: Optional[str] = None
#     page: Optional[str] = None
#     start: Optional[str] = None
#     limit: Optional[str] = None
#     limit_value: Optional[int] = 30
#
#     def get_next(self, result, page_num):
#         if page_num == 0:
#             return {self.limit: self.limit_value} if self.limit else {}
#         if self.next_page:
#             if result[self.next_page]:
#                 return parse.parse_qs(parse.urlsplit(result[self.next_page]).query)
#         elif self.start:
#             return {self.start: page_num*self.limit_value, self.limit: self.limit_value}
#         elif self.page:
#             if self.pages and page_num == result[self.pages]:
#                 return
#             return {self.page: page_num}
#
#     def __init__(self, parent):
#         self.page_num = 0
#         self.parent = parent
#
#     def __iter__(self):
#         return self
#
#     def __next__(self):
#         args = self.get_next(self.parent.result, self.page_num)
#         if args is None:
#             raise StopIteration
#         self.page_num += 1
#         return args
import aiohttp
from aiohttp import TCPConnector


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


class JsonEndpoint:
    url = "http://127.0.0.1:8888/users/{id}"
    params = {
        "foo": "bar",
        "page": range(0, 100),
        "category": [1, 2],
        "n": range(0, 100),
    }
    params_type = "params"
    url_params = {"id": range(1, 3)}
    results_key = "results"
    method = "get"
    good_statuses = [200]
    headers = {}
    cookies = {}
    proxy = None
    content_type = None

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

    async def request(self, url, **kwargs):
        async with self.session.request(self.method, url, **kwargs) as res:
            if res.status in self.good_statuses:
                try:
                    return await res.json(content_type=self.content_type)
                except JSONDecodeError:
                    return

    def _call_callables(self, params):
        if any(callable(value) for value in params.values()):
            return {
                key: value() if callable(value) else value
                for key, value in params.items()
            }
        return params

    def iter_params(self, params=None):
        if params is None:
            params = self.params
        for key, value in params.items():
            if iterable(value) and not isinstance(value, range):
                for i in value:
                    new_params = dict(params)
                    new_params[key] = i
                    yield self.iter_params(new_params)
                return
        ranges = [
            (key, value) for key, value in params.items() if isinstance(value, range)
        ]
        for key, value in ranges:
            for i in value:
                new_params = dict(params)
                new_params[key] = i
                if len(ranges) == 1:
                    yield from self.iter_params(new_params)
                else:
                    yield self.iter_params(new_params)
            return
        yield self._call_callables(params)

    def iter_urls(self, url_params=None):
        if url_params is None:
            url_params = self.iter_params(self.url_params)
        for params in url_params:
            if isinstance(params, dict):
                yield self.url.format(**params)
            else:
                yield self.iter_urls(params)

    def get_proxy(self):
        if iterable(self.proxy):
            return next(self.proxy)
        elif callable(self.proxy):
            return self.proxy()
        else:
            return self.proxy

    async def get_results(self, url, params):
        args = {
            self.params_type: params,
            "headers": self._call_callables(self.headers),
            "cookies": self._call_callables(self.cookies),
            "proxy": self.get_proxy(),
        }
        res = await self.request(url, **args)
        if res:
            if self.results_key:
                for key in self.results_key.split("."):
                    res = res.get(key)
        return res

    async def iter_results(self, iurls=None, iparams=None):
        if iurls is None:
            iurls = self.iter_urls()
        if iparams is None:
            iparams = self.iter_params()
        for url in iurls:
            if isinstance(url, str):
                for params in iparams:
                    if isinstance(params, dict):
                        results = await self.get_results(url, params)
                        if results:
                            for res in results:
                                yield res
                        else:
                            return
                    else:
                        async for res in self.iter_results([url], params):
                            yield res
            else:
                async for res in self.iter_results(url):
                    yield res


class NewEndpoint:
    url: str = "http://127.0.0.1:8888/users/{id}"
    params: Dict[
        str, Union[int, str, Iterable, AsyncGenerator, Awaitable, Callable]
    ] = {
        "foo": "bar",
        "page": range(0, 100),
        "category": [1, 2],
        "n": range(0, 100),
    }
    params_type = "params"
    url_params: Dict[
        str, Union[int, str, Iterable, AsyncGenerator, Awaitable, Callable]
    ] = {"id": range(1, 3)}
    results_key = "results"
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
        if not session:
            connector = TCPConnector(
                limit=self.limit, limit_per_host=self.limit_per_host
            )
            session = aiohttp.ClientSession(connector=connector)
        self.session = session or aiohttp.ClientSession()
        for key, value in kwa 1rgs.items():
            if not hasattr(self, key):
                raise AttributeError(f"{self} has no attribute {key}")
            if isinstance(getattr(self, key), dict):
                setattr(self, key, dict(getattr(self, key)))
                getattr(self, key).update(value)
            else:
                setattr(self, key, value)
        if self.params_type not in ["params", "data", "json"]:
            raise AttributeError(f'params_type should be "params", "data" or "json"')

    async def request(self, url, **kwargs):
        async with self.session.request(self.method, url, **kwargs) as res:
            if res.status in self.good_statuses:
                try:
                    return await res.json(content_type=None)
                except JSONDecodeError:
                    return

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
                yield self.url.format(**params)
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

    async def get_results(self, url, params):
        args = {
            self.params_type: params,
            "headers": await self._call_callables(self.headers),
            "cookies": await self._call_callables(self.cookies),
            "proxy": await self.get_proxy(),
        }
        res = await self.request(url, **args)
        if res:
            if self.results_key:
                for key in self.results_key.split("."):
                    if not isinstance(res, (list, dict)):
                        return
                    try:
                        res = res[key]
                    except (IndexError, KeyError):
                        res = None
        return res

    async def _iter_url(self, url):
        yield url

    async def iter_results(self, iurls=None, iparams=None):
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
                                yield res
                        else:
                            return
                    else:
                        async for res in self.iter_results(self._iter_url(url), params):
                            yield res
            else:
                async for res in self.iter_results(url):
                    yield res
