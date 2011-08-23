import functools
import inspect
import textwrap


cached = functools.lru_cache(maxsize=None)


def transform(cls):
    for interface in cls.__interfaces__:
        for name, value in vars(interface).items():
            if name.startswith('_') or isinstance(value, InterfaceDescriptor):
                continue
            original = getattr(cls, name)
            if inspect.isfunction(value):
                descriptor = InterfaceMethod
            else:
                descriptor = InterfaceAttribute
            setattr(cls, name, descriptor(name, original))
    return cls


def implements(*interfaces, transformer=transform):
    def decorator(cls):
        ifaces = interfaces
        try:
            ifaces = tuple(i for i in ifaces if i not in cls.__interfaces__)
            cls.__interfaces__ += ifaces
        except AttributeError:
            cls.__interfaces__ = ifaces
        if __debug__:
            for interface in ifaces:
                interface.__validate__(cls)
            if transformer is not None:
                cls = transformer(cls)
        return cls
    return decorator


class This:
    ...


class InterfaceError (Exception):
    ...


class InterfaceMeta (type):

    def __prepare__(name, bases):
        return {name: This}

    def __new__(cls, name, bases, vars):
        del vars[name]
        return super().__new__(cls, name, bases, vars)

    def __subclasscheck__(self, subclass):
        return self in getattr(subclass, '__interfaces__', ())

    def __instancecheck__(self, instance):
        return self in getattr(instance, '__interfaces__', ())


class Interface (metaclass=InterfaceMeta):

    def __invariant__(self):  # pragma: no cover
        ...

    @classmethod
    def __validate__(interface, cls):
        for name, value in vars(interface).items():
            if name.startswith('_'):
                continue

            assert hasattr(cls, name), assert_msg(
                """expected attribute or method missing
                {class}.{name} must be present to correctly implement the
                {interface} interface.
                """, cls, interface, name,
            )

            if not inspect.isfunction(value):
                continue

            assert inspect.isfunction(getattr(cls, name)), assert_msg(
                """attribute expected to be a method
                {class}.{name}() must be a function (typically an unbound
                method) to correctly implement the {interface} interface.
                """, cls, interface, name,
            )

            concrete = argspec(cls, name)
            abstract = argspec(interface, name)
            if concrete.varkw is None:
                assert set(abstract.args) <= set(concrete.args), assert_msg(
                    """method is missing expected arguments
                    {class}.{name}{concrete} must be compatible with the
                    signature {name}{abstract} to correctly implement the
                    {interface} interface, but is missing the arguments
                    {missing}.
                    """, cls, interface, name,
                    concrete=inspect.formatargspec(*concrete[:3]),
                    abstract=inspect.formatargspec(*abstract[:3]),
                    missing=set(abstract.args) - set(concrete.args),
                )

    @classmethod
    def __enforce__(interface, instance, name, args):
        spec = argspec(interface, name)

        for key, value in spec.annotations.items():
            if key == 'return':
                continue
            if value is This:
                value = interface

            assert isinstance(args[key], value), assert_msg(
                """method called with argument of unexpected type
                {class}.{name}() was called with {argument}={value!r}, but
                the {interface} interface suggests the argument must be an
                instance of {type!r}.
                """, type(instance), interface, name,
                argument=key, type=value, value=args[key],
            )

        kwargs = {key: value for key, value in args.items()
                  if key in spec.args or key in spec.kwonlyargs}
        method = getattr(interface, name)
        generator = method(**kwargs)
        if not inspect.isgeneratorfunction(method):
            yield
            return

        next(generator)
        result = yield

        if 'return' in spec.annotations:
            assert isinstance(result, spec.annotations['return'])

        try:
            generator.send(result)
        except StopIteration:
            pass
        else:
            raise InterfaceError('multiple yields in abstract method')

        interface.__invariant__(instance)


class InterfaceDescriptor:

    def __init__(self, name, original):
        self.name = name
        self.original = original


class InterfaceAttribute (InterfaceDescriptor):

    def __init__(self, name, original):
        super().__init__(name, original)
        self.instances = {}

    def __get__(self, instance, owner):
        if owner is None:  # pragma: no cover
            return self.original
        try:
            return self.instances[id(instance)]
        except KeyError:
            return self.original

    def __set__(self, instance, value):
        if value != self.original:
            for interface in instance.__interfaces__:
                self.validate(instance, interface, value)
        self.instances[id(instance)] = value

    def validate(self, instance, interface, value):
        attr = getattr(interface, self.name)

        if isinstance(attr, type):
            assert isinstance(value, attr), assert_msg(
                """tried to set an attribute to an unexpected type
                {class}.{name} must be an instance of {type!r} to correctly
                implement the {interface} interface, but {value!r} is a
                {value.__class__}.
                """, type(instance), interface, self.name,
                type=attr, value=value,
            )

        elif isinstance(attr, range):
            assert value in attr, assert_msg(
                """tried to set an attribute out of expected range
                {class}.{name} must be in {range!r} to correctly implement
                the {interface} interface, but {value!r} is not.
                """, type(instance), interface, self.name,
                range=attr, value=value,
            )


class InterfaceMethod (InterfaceDescriptor):

    def __get__(self, instance, owner):
        if owner is None:  # pragma: no cover
            return self.original
        return self.create_wrapper(instance)

    @cached
    def create_wrapper(self, instance):
        @functools.wraps(self.original)
        def wrapper(*args, **kwargs):
            callargs = inspect.getcallargs(self.original, instance,
                                           *args, **kwargs)
            enforcers = [
                interface.__enforce__(instance, self.name, callargs)
                for interface in instance.__interfaces__
                if hasattr(interface, self.name)
            ]
            for enforcer in enforcers:
                next(enforcer)
            result = self.original(instance, *args, **kwargs)
            for enforcer in enforcers:
                try:
                    enforcer.send(result)
                except StopIteration:
                    pass
                else:
                    raise InterfaceError('multiple yields in __enforce__')
            return result
        return wrapper


def assert_msg(template, cls, interface, name, **context):
    summary, details = template.rsplit('\n', 1)
    details = textwrap.fill(inspect.cleandoc(details))
    context['class'] = dotted(cls)
    context['interface'] = dotted(interface)
    context['name'] = name
    return '{}\n\n{}'.format(summary, details).format(**context)


@cached
def argspec(cls, name):
    return inspect.getfullargspec(getattr(cls, name))


@cached
def dotted(object):
    return '{0.__module__}:{0.__name__}'.format(object)
