import json
from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional
from typing import Protocol
from typing import Type
from typing import runtime_checkable

from sunflower.core.custom_types import BroadcastType
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


@runtime_checkable
class PersistentAttributesObject(Protocol):
    __data_type__: str
    __id__: str
    __keys__: set[str]


class PersistenceMixin:
    repository: Repository

    async def retrieve_from_repository(
            self,
            obj: PersistentAttributesObject,
            key: str,
            object_hook: Optional[Callable] = None):
        return await self.repository.retrieve(
            f"sunflower:{obj.__data_type__}:{obj.__id__}:{key}", object_hook)

    async def persist_to_repository(
            self,
            obj: PersistentAttributesObject,
            key: str,
            value: Any,
            json_encoder_cls: Optional[Type[json.JSONEncoder]] = None):
        return await self.repository.persist(
            f"sunflower:{obj.__data_type__}:{obj.__id__}:{key}", value, json_encoder_cls)

    async def publish_to_repository(
            self,
            obj: PersistentAttributesObject,
            channel: str,
            data: str):
        return await self.repository.publish(
            f"sunflower:{obj.__data_type__}:{obj.__id__}:{channel}", data)
