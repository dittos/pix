from typing import Callable, Type, TypeVar
from typing_extensions import Annotated, get_type_hints, get_args, get_origin

from pydantic_settings import BaseSettings

T = TypeVar("T")


class Value:
    def __init__(self, key: str):
        self.key = key


class Graph:
    def __init__(self, settings: BaseSettings = None):
        self._cache = {}
        self._factories = {}
        self._settings = settings
        if settings:
            self.bind_instance(type(settings), settings)
    
    def bind_instance(self, type: Type[T], instance: T):
        self._cache[type] = instance
    
    def bind_factory(self, type: Type[T], factory: Callable[..., T]):
        self._factories[type] = factory

    def get_instance(self, type: Type[T]) -> T:
        cached = self._cache.get(type)
        if cached is not None:
            return cached

        try:
            custom_factory = self._factories.get(type)
            func = custom_factory or type.__init__
            factory = custom_factory or type
            type_hints = get_type_hints(func, include_extras=True)
            kwargs = {}
            for name, annotation in type_hints.items():
                if name == "return": continue
                kwargs[name] = self._get_instance_from_annotation(name, annotation)
            
            instance = factory(**kwargs)
            self._cache[type] = instance
            return instance
        except Exception as e:
            raise ValueError(f"error while instantiating {type}", e)
    
    def _get_instance_from_annotation(self, name: str, annotation):
        if get_origin(annotation) is Annotated:
            _, *hints = get_args(annotation)
            for hint in hints:
                if hint is Value:
                    hint = Value(name)
                if isinstance(hint, Value):
                    return getattr(self._settings, hint.key)

        return self.get_instance(annotation)
