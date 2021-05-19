import json
from datetime import datetime
from json.encoder import JSONEncoder
from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional
from typing import Type

from sunflower.core.custom_types import BroadcastType
from sunflower.core.custom_types import NotifyChangeStatus
from sunflower.core.repository import Repository


class MetadataEncoder(json.JSONEncoder):
    """Subclass of json.JSONEncoder supporting BroadcastType serialization."""
    def default(self, obj):
        if isinstance(obj, BroadcastType):
            return obj.value
        return json.JSONEncoder.default(self, obj)


def as_metadata_type(mapping: Dict[str, Any]) -> Dict[str, Any]:
    """object_hook for supporting BroadcastType at json deserialization."""
    for k, v in mapping.items():
        if isinstance(v, BroadcastType):
            mapping[k] = v.value
            break
    return mapping


class PersistenceMixin:
    def __init_subclass__(cls, **kwargs):
        if not hasattr(cls, "data_type"):
            raise TypeError("Class using PersistenceMixin must have a"
                            "'data_type' class attribute.")

    def __init__(self, repository: Repository, __id: str, *args, **kwargs):
        self.repository = repository
        self.id = __id
        super().__init__(*args, **kwargs)

    def retrieve_from_repository(self, key: str, object_hook: Optional[Callable] = None):
        return self.repository.retrieve(
            f"sunflower:{self.data_type}:{self.id}:{key}", object_hook)

    def persist_to_repository(self, key: str, value: Any, json_encoder_cls: Optional[Type[json.JSONEncoder]] = None):
        return self.repository.persist(
            f"sunflower:{self.data_type}:{self.id}:{key}", value, json_encoder_cls)

    def publish_to_repository(self, channel, data):
        return self.repository.publish(
            f"sunflower:{self.data_type}:{self.id}:{channel}", data)



class PersistentAttribute:
    """Descriptor for attributes stored in external persistence system.

    For the moment, only Redis persistent attributes are implemented.

    Owner class or object must have two mandatory attributes:

    - `data_type`: the type of the object to which data belongs to (for example station or channel)
    - `endpoint`: a string identifying the object (for Channel objects it is also the endpoint for webapp)

    You can provide an boolean argument for notifying changes:

    - `notify_change`: if stored data is changed, this attribute will publish to a Redis channel with obj.endpoint name.
      If data is changed, the message will be NotifyChangeStatus.UPDATED = 1, else NotifyChangeStatus.UNCHANGED = 0
      If this attribute is set to None, it will only notify UNCHANGED.

    Hooks can be added for customizing persistence and retrievals:

    - `pre_set_hook_func()` is called before storing data in Redis database (see `__set__()` method).
    - `post_get_hook_func()` is called after retrieving data from Redis database (see `__get__()` method).

    These can be added through the constructor or with decorators. For example:

    ```
    persistent_attribute = PersistentAttribute(...)

    @persistent_attribute.pre_set_hook
    def persistent_attribute(self, value):
        # format data to be stored in Redis database
        return data

    @persistent_attribute.post_get_hook
    def persistent_attribute(self, data):
        # decode data
        return value
    ```
    """

    def __init__(
            self,
            key: str = "",
            doc: str = "",
            json_encoder_cls: Type[JSONEncoder] = MetadataEncoder,
            object_hook: Callable = as_metadata_type,
            notify_change: bool = False,
            pre_set_hook: Callable = lambda self, x: x,
            post_get_hook: Callable = lambda self, x: x):
        self.key = key
        self.__doc__ = doc
        self.json_encoder_cls = json_encoder_cls
        self.object_hook = object_hook
        self.notify_change = notify_change
        self.pre_set_hook_func = pre_set_hook
        self.post_get_hook_func = post_get_hook
        self._cache = None

    def __set_name__(self, owner, name):
        if not issubclass(owner, PersistenceMixin):
            raise TypeError("A PersistentAttribute must be defined in a class"
                            "inherting from 'PersitenceMixin'.")
        self.name = name
        if not self.__doc__:
            self.__doc__ = f"{self.name} persistent attribute."

    def __get__(self, obj: PersistenceMixin, owner):
        """Get data from Redis, and return self.post_get_hook_func(data)."""
        if obj is None:
            return self
        data = self._cache = obj.retrieve_from_repository(self.key, self.object_hook)
        return self.post_get_hook_func(obj, data)

    def __set__(self, obj: PersistenceMixin, value):
        """Pass value to self.pre_set_hook_func() and store the result in Redis database.

        data = self.pre_set_hook_func(obj, value) must be serializable.
        if value is None, notify unchanged or do nothing.
        """
        now = datetime.now().timestamp()
        data = self.pre_set_hook_func(obj, value) if value is not None else value
        if self._cache == data or data is None:
            if self.notify_change:
                obj.publish_to_repository("updates", NotifyChangeStatus.UNCHANGED.value)
            return
        obj.persist_to_repository(self.key, data, self.json_encoder_cls)
        self._cache = data
        if self.notify_change:
            obj.publish_to_repository("updates", NotifyChangeStatus.UPDATED.value)

    def __delete__(self, obj: PersistenceMixin):
        raise AttributeError(f"Can't delete attribute 'f{self.name}'.")

    def pre_set_hook(self, pre_set_hook_func):
        """Method for adding pre_set_hook_func() with a decorator.

        Usage:

        ```
        persistent_attribute = PersistentAttribute(...)

        @persistent_attribute.pre_set_hook
        def persistent_attribute(self, value):
            # format data to be stored in Redis database
            return data
        ```
        """
        return type(self)(
            self.key, self.__doc__, self.json_encoder_cls, self.object_hook,
            self.notify_change, pre_set_hook_func, self.post_get_hook_func)

    def post_get_hook(self, post_get_hook_func):
        """Method for adding post_get_hook_func() with a decorator.

        Usage:

        ```
        persistent_attribute = PersistentAttribute(...)

        @persistent_attribute.post_get_hook
        def persistent_attribute(self, data):
            # decode data
            return value
        ```
        """
        return type(self)(
            self.key, self.__doc__, self.json_encoder_cls, self.object_hook,
            self.notify_change, self.pre_set_hook_func, post_get_hook_func)
