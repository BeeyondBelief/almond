import contextlib
import inspect
import typing
from typing import Any, Callable, ClassVar, ContextManager, Dict, Generator, Generic, List, Tuple, \
    Type, TypeVar

from typing_extensions import Annotated

F = TypeVar('F', bound='XSupport')
T = TypeVar('T')
_XMagic = 42
_Spec = Tuple[str, Type[Any], Callable[..., Generator[Any, None, None]], List[Type[Any]]]

X = Annotated[T, _XMagic]
XContext = Dict[Type[Any], Callable[..., Generator[Any, None, None]]]


class _XTree:
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


class XSupport:
    __slots__ = ()
    _spec: ClassVar[List[_Spec]]
    _members: ClassVar[List[Tuple[str, Any]]] = []

    def __init_subclass__(cls, **kwargs: Any):
        for attr, type_hint in typing.get_type_hints(cls, include_extras=True).items():
            meta = getattr(type_hint, '__metadata__', None)
            if meta is not None and meta[0] == _XMagic:
                cls._members.append((attr, type_hint.__origin__))

    @staticmethod
    def _static_generator(gen_val: T) -> Callable[..., Generator[T, None, None]]:
        def f() -> Generator[T, None, None]:
            yield gen_val
        return f

    @classmethod
    def compile(cls, context: XContext) -> None:
        tree = _XTree()
        specs: List[_Spec] = []
        banned_args = {'self', 'cls'}
        for attr, origin in cls._members:
            generator = context.get(origin)
            if generator is None:
                static_val = getattr(cls, attr, None)
                if static_val is None:
                    continue
                generator = cls._static_generator(static_val)

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
                    f'все его зависимости удовлетворены. Для использования {X[{spec[1].__name__}]} '
                    f'необходимо наличие следующих объектов в классе "{cls.__name__}": '
                    f'{", ".join(f"X[{x.__name__}]" for x in tree.get_dependencies(spec[1]))}. '
                    f'Наличие требуемых объектов не обязательно в контексте, если '
                    f'назначено значение по умолчанию.'
                )
                raise TypeError(msg)
        # FIXME: Recursive dependencies
        cls._spec = sorted(specs, key=lambda x: tree.get_level(x[1]))


class XStaticProducer(Generic[T]):
    def __init__(self, gen_val: T) -> None:
        self.gen_val = gen_val

    def __call__(self) -> Generator[T, None, None]:
        yield self.gen_val


class A(XSupport):
    x: X[int]

    def do(self):
        print(self.x)


def main():
    context: XContext = {
        int: XStaticProducer(12),
    }
    A.compile(context)

    with xbuild(A) as a:
        a.do()


if __name__ == '__main__':
    main()
