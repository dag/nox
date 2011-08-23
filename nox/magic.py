import collections
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
