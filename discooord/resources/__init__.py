# Python 3 compatibility
try:
    import urlparse
except:
    from urllib import parse as urlparse

try:
    unicode = unicode
except:
    class unicode(str):
        pass


class ResourceMetaclass(type):
    def __new__(cls, name, bases, attrs):
        if name != 'Resource' and ('name' not in attrs or attrs['name'] is None):
            attrs['name'] = name.lower()

        parent_resource = attrs.get('parent_resource', None)
        if parent_resource is not None:
            if not issubclass(parent_resource, Resource):
                raise AttributeError('parent_resource must be a child of Resource or None')

            parent_resources = []
            parent = parent_resource

            while parent is not None:
                parent_resources.append(parent)
                parent = parent.parent_resource

            parent_resources.reverse()
            attrs['parent_resources'] = parent_resources

        return super(ResourceMetaclass, cls).__new__(cls, name, bases, attrs)


class Resource(object):
    '''Helper base for access API resources'''

    __metaclass__ = ResourceMetaclass

    name = None
    parent_resource = None
    parent_resources = None

    client = None

    def __init__(self, client):
        if client is None:
            raise ValueError('client')
        self.client = client

    @classmethod
    def register(cls, client):
        resource = cls(client)
        setattr(client, cls.__name__.lower(), resource)

    @classmethod
    def build_resource(cls, *primaries):
        url = []

        if cls.parent_resources is not None:
            parent_count = len(cls.parent_resources)
            primaries_count = len(primaries)

            for i, parent in enumerate(cls.parent_resources):
                url.append(parent.name)
                if i < primaries_count:
                    url.append(primaries[i])

            url.append(cls.name)

            if primaries_count > parent_count:
                url += primaries[parent_count:]
        else:
            url.append(cls.name)
            url += primaries

        return '/' + '/'.join([str(u) for u in url])

    def build_url(self, *primaries):
        resource = self.build_resource(*primaries)
        return resource


# __all__ registry to simplify things
from .oauth2 import OAuth2
from .gateway import Gateway
from .users import Users
from .channels import Channels, Messages

__all__ = [
    'OAuth2',
    'Gateway',
    'Users',
    'Channels',
    'Messages'
]
