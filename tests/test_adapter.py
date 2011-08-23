import io
import pytest

from collections import Sized, Mapping
from numbers import Number
from nox import adapter


class StringIO (io.StringIO):

    def __init__(self, initial_value: str):
        super().__init__(initial_value)


class NumberFormatter:

    def __call__(self, num: Number) -> str:
        return format(num, ',')

    def percentage(self, num: Number) -> str:
        return format(num / 100, '.1%')


def format_number(num: Number) -> str:
    return format(num, ',')


def pytest_funcarg__adapt(request):
    return adapter.Registry()


def pytest_funcarg__numformatter(request):
    return NumberFormatter()


def test_class_type_inference():
    expected = (str, StringIO)
    inferred = adapter.infer(StringIO)
    assert inferred == expected
    assert isinstance(inferred, adapter.Adaptation)


def test_callable_type_inference(numformatter):
    expected = (Number, str)
    inferred = adapter.infer(numformatter)
    assert inferred == expected
    assert isinstance(inferred, adapter.Adaptation)


def test_method_type_inference(numformatter):
    expected = (Number, str)
    inferred = adapter.infer(numformatter.percentage)
    assert inferred == expected
    assert isinstance(inferred, adapter.Adaptation)


def test_function_type_inference():
    expected = (Number, str)
    inferred = adapter.infer(format_number)
    assert inferred == expected
    assert isinstance(inferred, adapter.Adaptation)


def test_inplace_add(adapt):
    adapt += StringIO
    adapt += format_number
    assert adapt[str:StringIO] is StringIO
    assert adapt[Number:str] is format_number


def test_assignment(adapt):
    adapt[str:io.IOBase] = io.StringIO
    adapt[Sized:Number] = len
    assert adapt[str:io.IOBase] is io.StringIO
    assert adapt[Sized:Number] is len


def test_adapting(adapt):
    adapt += StringIO
    adapt += format_number
    assert adapt('hello', io.IOBase).read() == 'hello'
    assert adapt(5000, str) == '5,000'


def test_conforming(adapt):
    assert adapt(5000, Number) == 5000


def test_adaptation_error(adapt):
    with pytest.raises(adapter.AdaptationError) as e:
        adapt(5000, str)
    assert str(e.value) == 'no adaptation known for int -> str'


def test_alternate(adapt):
    assert adapt(5000, str, '5000') == '5000'


def test_recursion(adapt):
    adapt += format_number
    adapt[Sized:Number] = len
    assert adapt(range(1337), str) == '1,337'

    adapt[Number:range] = range
    adapt[range:list] = list
    assert adapt('hello', list) == [0, 1, 2, 3, 4]
