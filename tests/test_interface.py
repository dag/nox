import pytest

from nox.interface import Interface, implements


ifdebug = pytest.mark.xfail('not __debug__')


class People (Interface):

    first_name = str

    last_name = str

    age = range(0, 150)

    def __invariant__(self):
        assert self.first_name or self.last_name, 'i must have a name'

    def greet(self, person: People) -> str:
        assert person is not self, 'no talking to yourself'
        result = yield
        assert len(result) < 20, '*yawn*'


@implements(People)
class Person:

    first_name = None

    last_name = None

    age = None

    def greet(self, person):
        return 'Hello, {.first_name}!'.format(person)


def test_subclasscheck():
    assert issubclass(Person, People)


def test_instancecheck():
    assert isinstance(Person(), People)


@ifdebug
def test_typed_descriptors():
    person = Person()
    person.first_name = 'Guido'
    with pytest.raises(AssertionError) as e:
        person.first_name = 123
    assert 'tried to set an attribute to an unexpected type' in str(e.value)
    with pytest.raises(AssertionError) as e:
        person.age = 200
    assert 'tried to set an attribute out of expected range' in str(e.value)
    person.age = 50


@ifdebug
def test_missing_attributes():
    with pytest.raises(AssertionError) as e:
        @implements(People)
        class Person:
            first_name = last_name = greet = None
    assert 'expected attribute or method missing' in str(e.value)


@ifdebug
def test_incorrect_method():
    with pytest.raises(AssertionError) as e:
        @implements(People)
        class Person:
            first_name = last_name = age = None
            def greet(self): ...
    assert 'method is missing expected arguments' in str(e.value)


@ifdebug
def test_call_method_incorrect_type():
    person = Person()
    with pytest.raises(AssertionError) as e:
        person.greet('World')
    assert 'method called with argument of unexpected type' in str(e.value)


@ifdebug
def test_call_method_preconditions():
    person = Person()
    person.first_name = 'Guido'
    with pytest.raises(AssertionError) as e:
        person.greet(person)
    assert 'no talking to yourself' in str(e.value)


@ifdebug
def test_call_method_postconditions():
    person = Person()
    poppins = Person()
    poppins.first_name = 'Supercalifragilisticexpialidocious'
    with pytest.raises(AssertionError) as e:
        person.greet(poppins)
    assert '*yawn*' in str(e.value)


@ifdebug
def test_invariant():
    guido = Person()
    larry = Person()
    larry.first_name = 'Larry'
    with pytest.raises(AssertionError) as e:
        guido.greet(larry)
    assert 'i must have a name' in str(e.value)


def test_correct_call():
    guido = Person()
    guido.first_name = 'Guido'
    larry = Person()
    larry.first_name = 'Larry'
    assert guido.greet(larry) == 'Hello, Larry!'
