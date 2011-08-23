import inspect

from nox import magic


class Adaptation (magic.NamedTuple):

    adapted

    provided


class AdaptationError (TypeError):

    def __str__(self):
        string = 'no adaptation known for {} -> {}'
        types = (t.__name__ for t in self.args)
        return string.format(*types)


class Registry:

    def __init__(self):
        self._adapters = {}

    def __iadd__(self, factory):
        self._adapters[infer(factory)] = factory
        return self

    def __getitem__(self, path):
        try:
            return self._adapters[path.start, path.stop]
        except KeyError:
            for adapted, provided in self._adapters:
                if issubclass(provided, path.stop):
                    factory = self[adapted:provided]
                    if issubclass(path.start, adapted):
                        return factory
                    chain = self[path.start:adapted]
                    return lambda x: factory(chain(x))
            raise AdaptationError(path.start, path.stop)

    def __setitem__(self, path, factory):
        adaptation = Adaptation(path.start, path.stop)
        self._adapters[adaptation] = factory

    def __call__(self, object, protocol, alternate=...):
        if isinstance(object, protocol):
            return object
        try:
            return self[type(object):protocol](object)
        except AdaptationError:
            if alternate is ...:
                raise
        return alternate


def infer(factory):
    arg = 1  # compensate for 'self'
    provided = None

    if inspect.isclass(factory):
        provided = factory
        factory = factory.__init__

    elif inspect.isfunction(factory):
        arg = 0

    elif not inspect.ismethod(factory):
        factory = factory.__call__

    signature = inspect.getfullargspec(factory)
    adapted = signature.annotations[signature.args[arg]]
    if provided is None:
        provided = signature.annotations['return']
    return Adaptation(adapted, provided)
