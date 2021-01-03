import enum
import inspect
from dataclasses import dataclass
from typing import Dict, Union, Tuple, List, Optional

from .base import Endpoint
from bs4 import BeautifulSoup, Tag


class SelectTypes(enum.Enum):
    soup = 'soup'
    text = 'text'
    attrs = 'attrs'
    attr = 'attr'
    fun = 'fun'


def selector_defaults(cls):
    defaults = {'many': True, 'type': SelectTypes.soup.value}
    for k, v in defaults.items():
        if not hasattr(cls, k):
            setattr(cls, k, v)
    if not hasattr(cls, 'selector'):
        raise AttributeError('Selector class shoud have selector attribute with css selector stri')
    if cls.type == SelectTypes.attr.value and not hasattr(cls, 'attr'):
        raise AttributeError('Selector class of type attr should have attr attribute with name of attr to get')
    return cls


class HtmlEndpoint(Endpoint):
    """
    Example of selector attribute:

    class myEndpoing(HtmlEndpoint):
        class selector:
            selector = "div.body"
            many = False

            class h2s:
                selector = "h2 a:first-child"
                many = True
                type = "text"

    """
    selector: type

    def select_by_class(self, soup, obj):
        obj = selector_defaults(obj)
        subs = {name: sub for name, sub in inspect.getmembers(obj) if not name.startswith('_') and isinstance(sub, type)}
        tags = soup.select(obj.selector) if obj.many else soup.select_one(obj.selector)
        if subs:
            if obj.many:
                return [{name: self.select_by_class(tag, sub) for name, sub in subs.items()} for tag in tags]
            else:
                return {name: self.select_by_class(tags, sub) for name, sub in subs.items()}

        if obj.type == SelectTypes.text.value:
            return getattr(tags, 'text', '') if not obj.many else [isinstance(tag, Tag) and getattr(tags, 'text', '') for tag in tags]
        elif obj.type == SelectTypes.attrs.value:
            return tags.attrs if not obj.many else [isinstance(tag, Tag) and tag.attrs for tag in tags]
        elif obj.type == SelectTypes.attr.value:
            return tags.attrs.get(obj.attr) if not obj.many else [isinstance(tag, Tag) and tag.attrs.get(obj.attr) for
                                                                  tag in tags]
        elif obj.type == SelectTypes.fun.value:
            return obj.fun(tags) if not obj.many else [isinstance(tag, Tag) and obj.fun(tags) for tag in tags]

    async def fetch(self, response):
        res = await response.text()
        if res:
            return BeautifulSoup(res, 'html.parser')

    def transform(self, results):
        if results:
            if not hasattr(self, 'selector') or not isinstance(self.selector, type):
                raise AttributeError('You have to define "selector" class inside endpoint')
            return self.select_by_class(results, self.selector)
