from typing_extensions import Annotated

from pydantic_settings import BaseSettings
from pixdb.inject import Graph, Value


class B:
    def __init__(self):
        pass


class A:
    def __init__(self, b: B, b2: "B"):
        self.b = b
        self.b2 = b2


class Values:
    def __init__(self, token: Annotated[str, Value], aliased: Annotated[str, Value("token")]) -> None:
        self.token = token
        self.aliased = aliased


def test_auto_instantiation():
    graph = Graph()
    a = graph.get_instance(A)
    assert isinstance(a, A)
    assert isinstance(a.b, B)

    assert graph.get_instance(A) is a
    assert graph.get_instance(B) is a.b


def test_bind_instance():
    graph = Graph()
    b = B()
    graph.bind_instance(B, b)
    assert graph.get_instance(B) is b


def test_bind_factory():
    def factory(b: B):
        a = A(b, b)
        a._from_factory = True
        return a
    
    graph = Graph()
    graph.bind_factory(A, factory)
    a = graph.get_instance(A)
    assert a._from_factory
    assert graph.get_instance(A) is a
    assert graph.get_instance(B) is a.b


def test_inject_settings_value():
    class Settings(BaseSettings):
        token: str

    settings = Settings(token="token")
    graph = Graph(settings)
    values = graph.get_instance(Values)
    assert values.token == settings.token
    assert values.aliased == settings.token
    assert graph.get_instance(Settings) is settings


def test_bind_implementation():
    class Interface:
        def a(self): ...
    
    class Implementation:
        def a(self): return "hi"
    
    graph = Graph()
    graph.bind_implementation(Interface, Implementation)
    assert isinstance(graph.get_instance(Interface), Implementation)


def test_run():
    def f(b: B):
        return b

    graph = Graph()
    assert isinstance(graph.run(f), B)
