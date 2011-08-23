from nox import magic


outer = ...


class MagicTuple (magic.NamedTuple):

    keeps_order

    _ignores_private

    and_not_sorted_lexically

    whoa_man

    outer


def test_named_tuple():
    magical = MagicTuple(1, 2, 3, 4)
    assert isinstance(magical, tuple)
    assert magical.keeps_order is magical[0] is 1
    assert magical.and_not_sorted_lexically is magical[1] is 2
    assert magical.whoa_man is magical[2] is 3
    assert magical.outer is magical[3] is 4


def test_placeholder():
    X = magic.X

    words = ['hello', 'world']
    assert list(map(X.upper(), words)) == ['HELLO', 'WORLD']

    class Person (magic.NamedTuple):

        first_name

        last_name

    people = [Person('Guido', 'van Rossum'), Person('Larry', 'Wall')]
    assert list(map(X.first_name, people)) == ['Guido', 'Larry']
    assert list(map(X[1], people)) == ['van Rossum', 'Wall']

    numbers = [3, 6, 9]
    assert list(map(X * 3, numbers)) == [9, 18, 27]
