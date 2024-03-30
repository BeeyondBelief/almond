import typing
from typing import Any, ClassVar, List, Tuple, TypeVar

from typing_extensions import Annotated

from .resolver import AlmondContext, AlmondSpec, resolve

_T = TypeVar('_T')
_MAGIC_INT = 42

Almond = Annotated[_T, _MAGIC_INT]


class AlmondSupport:
    __slots__ = ()
    _spec: ClassVar[List[AlmondSpec]]

    @classmethod
    def get_almond_members(cls) -> List[Tuple[str, Any]]:
        members: List[Tuple[str, Any]] = []
        for attr, type_hint in typing.get_type_hints(cls, include_extras=True).items():
            meta = getattr(type_hint, '__metadata__', None)
            if meta is not None and meta[0] == _MAGIC_INT:
                members.append((attr, type_hint.__origin__))
        return members

    @classmethod
    def compile(cls, context: AlmondContext) -> None:
        cls._spec = resolve(cls, context)
