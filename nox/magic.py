import collections
import functools
import operator


class _FieldRecordingDict (dict):

    def __init__(self):
        super().__init__(_fields=[])

    def __missing__(self, key):
        if not key.startswith('_'):
            self['_fields'].append(key)


class _NamedTupleMeta (type):

    def __prepare__(name, bases):
        return _FieldRecordingDict()

    def __new__(cls, name, bases, ns):
        return collections.namedtuple(name, ns['_fields'])


NamedTuple = type.__new__(_NamedTupleMeta, 'NamedTuple', (), {})


class _PlaceholderMeta (type):

    _OPS = {
        'add', 'sub', 'mul', 'truediv', 'floordiv',
        'mod', 'pow', 'lshift', 'rshift',
        'and', 'xor', 'or',
    }

    def _make_placeholder_op(name):
        func = getattr(operator, name)
        return lambda x, y: lambda i: func(i, y)

    def __new__(cls, name, bases, ns):
        for op in cls._OPS:
            op = '__{}__'.format(op)
            ns[op] = cls._make_placeholder_op(op)
        return type.__new__(cls, name, bases, ns)


class _Placeholder (metaclass=_PlaceholderMeta):

    def __getattr__(self, name):
        def key(item=...):
            if item is ...:
                return operator.methodcaller(name)
            return getattr(item, name)
        return key

    def __getitem__(self, item):
        return operator.itemgetter(item)


X = _Placeholder()


@functools.total_ordering
class _EnumValue:

    def __init__(self, enum, name, position):
        self.enum, self.name, self.position = enum, name, position

    def __repr__(self):
        return '{self.enum.__name__}.{self.name}'.format(self=self)

    def __lt__(self, other):
        return self.position < other.position

    def __index__(self):
        return self.position

    def __add__(self, other):
        return list(self.enum)[self.position + operator.index(other)]

    def __sub__(self, other):
        return list(self.enum)[self.position - operator.index(other)]

    def __contains__(self, other):
        return self is other


class _EnumMeta (type):

    def __prepare__(name, bases):
        return _FieldRecordingDict()

    def __new__(cls, enum, bases, ns):
        enum = type.__new__(cls, enum, (), {})
        for position, name in enumerate(ns['_fields']):
            setattr(enum, name, _EnumValue(enum, name, position))
        return enum

    def __iter__(cls):
        values = (value for value in vars(cls).values()
                        if isinstance(value, _EnumValue))
        return iter(sorted(values, key=X.position))

    def __repr__(cls):
        return '<{} ({})>'.format(cls.__name__,
                                  ', '.join(value.name for value in cls))


Enum = type.__new__(_EnumMeta, 'Enum', (), {})
