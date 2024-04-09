import abc
from typing import Generator, Generic, TypeVar, Callable

T = TypeVar('T')


class AlmondProducer(Generic[T], abc.ABC):
    @abc.abstractmethod
    def __call__(self) -> Generator[T, None, None]: ...


class StaticAlmondProducer(AlmondProducer[T], Generic[T]):
    def __init__(self, gen_val: T) -> None:
        self.gen_val = gen_val

    def __call__(self) -> Generator[T, None, None]:
        yield self.gen_val


class DynamicAlmondProducer(AlmondProducer[T], Generic[T]):
    def __init__(self, gen: Callable[[], T]) -> None:
        self.gen = gen

    def __call__(self) -> Generator[T, None, None]:
        yield self.gen()
