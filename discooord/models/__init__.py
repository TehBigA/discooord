from copy import copy
import json
import re

from ..exceptions import UnknownOperation
from ..utils import get_logger, Bunch

# Python 3 compatibility
try:
    long = long
except:
    class long(int):
        pass

try:
    unicode = unicode
except:
    class unicode(str):
        pass


_LOG = get_logger('discooord')


# Discord unique identifier
class snowflake(str):
    pass


class omit:
    pass


class ModelMetaclass(type):
    def __new__(cls, name, bases, attrs):
        if name != 'Model':
            if 'spec' in attrs and 'spec' is not None and not isinstance(attrs['spec'], dict):
                # Spec is a single piece of data, not an object
                attrs['_spec'] = attrs.pop('spec')
            else:
                # Spec is object of fields, merge into copies of base class specs
                spec = {}

                # TODO: Recursive to future proof
                for base in reversed(bases):
                    if not hasattr(base, '_spec'):
                        continue

                    for k, v in base._spec.iteritems():
                        if isinstance(v, (tuple, list, dict)):
                            spec[k] = copy(v)
                        else:
                            spec[k] = v

                spec.update(attrs.pop('spec', {}))

                attrs['_spec'] = spec

        return super(ModelMetaclass, cls).__new__(cls, name, bases, attrs)


class Model(object):
    '''Model object returned by API or pushed through it.'''

    __metaclass__ = ModelMetaclass

    _initialized = None
    _data = None

    def __init__(self, data=None, **kwargs):
        self._initialized = set()
        self._data = data or kwargs

    def get(self, key, default=None):
        if key not in self._spec:
            raise AttributeError("'{}' object has no attribute '{}'".format(self.__class__.__name__, key))

        if key in self._initialized:
            return self._data.get(key, default)

        spec = self._spec[key]
        value = self._data.pop(key, default)
        omit_value = (value == omit or isinstance(value, omit))

        if value is not None and not omit_value:
            if isinstance(spec, (tuple, list)):
                container = type(spec)
                containee = spec[0]

                value = container([containee(v) for v in value])
            elif isinstance(spec, dict):
                # TODO: Recursive model instead??
                value = Bunch(**value)
            elif spec is not None:
                value = spec(value)

        if not omit_value:
            self._data[key] = value

        self._initialized.add(key)

        return value

    def set(self, key, value, uninitialized=False):
        if key in ('_initialized', '_data', '_spec'):
            super(Model, self).__setattr__(key, value)
            return

        if not uninitialized:
            self._initialized.add(key)
        else:
            self._initialized.remove(key)

        self._data[key] = value

    __getattr__ = get
    __setattr__ = set

    def spec(self, key):
        spec = self._spec[key]
        container = None

        if isinstance(spec, (tuple, list)):
            container = type(spec)
            spec = spec[0]

        return spec, container

    def as_dict(self):
        # Initialize all attributes
        for field, spec in self._spec.iteritems():
            getattr(self, field)

        return self._data

    def merge(self, source):
        '''
            Merges `source` data and initialize state into self.
            Warning: Will copy references.
        '''

        for k, v in source._data.iteritems():
            self._data[k] = v

            # Update initialize states
            if k in source._initialized:
                self._initialized.add(k)
            else:
                self._initialized.remove(k)


class ModelEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Model):
            return obj.as_dict()
        elif isinstance(obj, Bunch):
            return obj.__dict__
        super(ModelEncoder, self).default(obj)


class HandlerMixin(object):
    '''A model mixin that has a `handle` method for processing payloads'''

    dispatch_code = None

    def handle(self, client):
        pass


class DispatchableMixin(object):
    '''A model mixin that has a `dispatch` method and `register` class method for handlers of certain payloads'''

    _HANDLERS = None
    _HANDLERS_INVERSE = None

    dispatch_key = None
    dispatch_data_key = 'd'

    @classmethod
    def register(cls, code=None):
        def wrapped(handler):
            final_code = code
            if final_code is None:
                final_code = '_'.join(map(str.upper, re.findall(r'[A-Z][a-z]+', handler.__name__)))

            if not issubclass(handler, HandlerMixin):
                raise ValueError('handler')

            cls._HANDLERS = cls._HANDLERS or {}
            cls._HANDLERS_INVERSE = cls._HANDLERS_INVERSE or {}

            cls._HANDLERS[final_code] = handler
            cls._HANDLERS_INVERSE[handler] = final_code

            handler.dispatch_code = final_code

            return handler

        return wrapped

    @classmethod
    def get_code(cls, handler):
        handler = handler if isinstance(handler, type) else handler.__class__
        return cls._HANDLERS_INVERSE[handler]

    def dispatch(self, client):
        code = getattr(self, self.__class__.dispatch_key)
        if code not in self.__class__._HANDLERS:
            raise UnknownOperation(code)

        handler_class = self.__class__._HANDLERS[code]

        if issubclass(handler_class, DispatchableMixin):
            # Pass original payload on to other dispatchers
            handler = handler_class(self._data)
        else:
            # Pass on embedded payload
            data = self.__class__.dispatch_data_key
            handler = handler_class(getattr(self, data))

        try:
            handler.handle(client)
            '''self.on_dispatch(client, handler)'''
        except:
            _LOG.error('Handler call failed ({})'.format(handler), exc_info=True)
