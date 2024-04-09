import sys
import typing
from typing import Any, ClassVar, Dict, List, Tuple, TypeVar

from typing_extensions import Annotated

from almond.resolver import AlmondContext, AlmondSpec, resolve

if sys.version_info >= (3, 8):
    def _get_type_hints(cls: object) -> Dict[str, Any]:
        return typing.get_type_hints(cls, include_extras=True)
else:
    _get_type_hints = typing.get_type_hints


_T = TypeVar('_T')
_MAGIC_INT = 42

Almond = Annotated[_T, _MAGIC_INT]


class AlmondSupport:
    __slots__ = ()
    _spec: ClassVar[List[AlmondSpec]]

    @classmethod
    def get_almond_members(cls) -> List[Tuple[str, Any]]:
        members: List[Tuple[str, Any]] = []
        for attr, type_hint in _get_type_hints(cls).items():
            meta = getattr(type_hint, '__metadata__', None)
            if meta is not None and meta[0] == _MAGIC_INT:
                members.append((attr, type_hint.__origin__))
        return members

    @classmethod
    def compile(cls, context: AlmondContext) -> None:
        cls._spec = resolve(cls, context)
