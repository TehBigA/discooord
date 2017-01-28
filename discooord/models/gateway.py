from . import Model, DispatchableMixin, HandlerMixin
#from ..exceptions import UnknownOperation


__all__ = ['GatewayPayload', 'PayloadHandler', 'GatewayOperation', 'GatewayEvent']


class BuildablePayload(object):
    def build(self):
        raise NotImplementedError('Build method not implemented')


class GatewayPayload(Model, DispatchableMixin):
    spec = {
        'op': int,
        'd': None,
        's': int,
        't': str
    }


class GatewayOperationDispatcher(GatewayPayload):
    dispatch_key = 'op'


class GatewayOperation(Model, HandlerMixin, BuildablePayload):
    '''Classification base class'''

    def build(self):
        '''Builds outgoing payload'''

        return {
            'op': GatewayOperationDispatcher.get_code(self),
            'd': self
        }


@GatewayOperationDispatcher.register(0)
class GatewayEventDispatcher(GatewayPayload, HandlerMixin):
    dispatch_key = 't'

    '''def on_dispatch(self, client, handler):
        client.on_event(handler)'''

    def handle(self, client):
        self.dispatch(client)


class GatewayEvent(Model, HandlerMixin, BuildablePayload):
    '''Classification base class'''

    # TODO: allow on_event to stop progression
    def handle(self, client):
        client.on_event(self.dispatch_code, self)

    def build(self):
        '''Builds outgoing payload'''

        return {
            'op': 0,
            'd': self,
            't': GatewayEventDispatcher.get_code(self)
        }

# Trigger registration
from .operations import *
from .events import *
