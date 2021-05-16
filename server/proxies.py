import abc

from sunflower.core.persistence import PersistenceMixin
from sunflower.core.repository import Repository


class Proxy(abc.ABC, PersistenceMixin):
    data_type = abc.abstractproperty()

    def __getattr__(self, name):
        return self.retrieve_from_repository(name)


class ChannelProxy(Proxy):
    data_type = "channel"


class PycoloreProxy(Proxy):
    data_type = "station"

    def __init__(self, repository: Repository, *args, **kwargs):
        super().__init__(repository, "pycolore", *args, **kwargs)
