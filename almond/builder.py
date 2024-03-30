import contextlib
from typing import Any, ContextManager, Dict, Generator, List, Type, TypeVar

from almond.support import AlmondSupport

F = TypeVar('F', bound=AlmondSupport)

@contextlib.contextmanager
def xbuild(x: Type[F]) -> ContextManager[F]:
    _active_generators: List[Generator[Any, None, None]] = []
    _cached: Dict[type, object] = {}

    inst = x.__new__(x)
    for attr, origin, non_initialized_gen, dependencies in x._spec:
        if dependencies:
            gen = non_initialized_gen(*(_cached[r] for r in dependencies))
        else:
            gen = non_initialized_gen()
        _active_generators.append(gen)
        initialized_value = next(gen)
        _cached[origin] = initialized_value
        setattr(inst, attr, initialized_value)
    try:
        yield inst
    finally:
        for g in reversed(_active_generators):
            for _ in g:
                pass
