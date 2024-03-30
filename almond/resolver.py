import inspect
from typing import Any, Callable, Dict, Generator, List, TYPE_CHECKING, Tuple, Type

from almond.producer import AlmondProducer, StaticAlmondProducer

if TYPE_CHECKING:
    from almond.support import AlmondSupport


AlmondSpec = Tuple[str, Type[Any], Callable[..., Generator[Any, None, None]], List[Type[Any]]]
AlmondContext = Dict[Type[Any], AlmondProducer]


class _AlmondTree:
    __slots__ = ('_tree',)

    def __init__(self) -> None:
        self._tree: Dict[Type[Any], List[Type[Any]]] = {}

    def add(self, o: Type[Any]) -> None:
        self._tree[o] = []

    def connect(self, o1: Type[Any], o2: Type[Any]) -> None:
        self._tree[o1].append(o2)

    def __getitem__(self, item):
        return self._tree[item]

    def get_level(self, o: Type[Any]) -> int:
        if self._tree.get(o) is None:
            return 0
        args = [self.get_level(x) for x in self._tree[o]]
        args.append(0)
        return max(args) + 1

    def has_all_dependencies(self, o: Type[Any]) -> bool:
        if self._tree.get(o) is None:
            return False
        if not self._tree[o]:
            return True
        return all(x in self._tree for x in self._tree[o])

    def get_dependencies(self, o: Type[Any]) -> List[Type[Any]]:
        return self._tree.get(o, [])


def resolve(obj: Type['AlmondSupport'], context: AlmondContext) -> List[AlmondSpec]:
    tree = _AlmondTree()
    specs: List[AlmondSpec] = []
    banned_args = {'self', 'cls'}
    for attr, origin in obj.get_almond_members():
        generator = context.get(origin)
        if generator is None:
            static_val = getattr(obj, attr, None)
            if static_val is None:
                continue
            generator = StaticAlmondProducer(static_val)

        arg_spec = inspect.getfullargspec(generator)
        dependencies = [arg_spec.annotations[x] for x in arg_spec.args if x not in banned_args]
        tree.add(origin)
        for d in dependencies:
            tree.connect(origin, d)
        specs.append((attr, origin, generator, dependencies))
    for spec in specs:
        if not tree.has_all_dependencies(spec[1]):
            msg = (
                f'Невозможно создать объект "{spec[0]} = X[{spec[1].__name__}]" так как не '
                f'все его зависимости удовлетворены. Для использования X{[{spec[1].__name__}]} '
                f'необходимо наличие следующих объектов в классе "{obj.__name__}": '
                f'{", ".join(f"X[{x.__name__}]" for x in tree.get_dependencies(spec[1]))}. '
                f'Наличие требуемых объектов не обязательно в контексте, если '
                f'назначено значение по умолчанию.'
            )
            raise TypeError(msg)
    return sorted(specs, key=lambda y: tree.get_level(y[1]))
