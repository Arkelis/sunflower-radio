from typing import Mapping
from functools import cache

from edn_format import Keyword as K
from edn_format import loads

__all__ = ('get_config', 'K')


@cache
def get_config(filename="conf.edn") -> Mapping:
    with open(filename) as f:
        return loads(f.read())
