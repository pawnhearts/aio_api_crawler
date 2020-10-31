import enum

from .base import Endpoint
from bs4 import BeautifulSoup


class SelectTypes(enum.Enum):
    soup = 'soup'
    text = 'text'
    attrs = 'attrs'


class HtmlEndpoint(Endpoint):
    selector: str
    select_one: bool = False
    select_type: SelectTypes = SelectTypes.soup.value

    def __init__(self, session=None, **kwargs):
        super().__init__(session, **kwargs)
        select_types = [stype.value for stype in SelectTypes]
        if self.select_type not in select_types:
            raise AttributeError(f'select_type should be in {repr(select_types)}')

    def transform(self, results):
        if results:
            soup = BeautifulSoup(results, 'html.parser')
            tags = soup.select_one(self.selector) if self.select_one else soup.select(self.selector)
            if self.select_type == SelectTypes.soup.value:
                return tags
            elif self.select_type == SelectTypes.text.value:
                return tags.text if self.select_one else [tag.text for tag in tags]
            elif self.select_type == SelectTypes.attrs.value:
                return tags.attrs if self.select_one else [tag.attrs for tag in tags]
