import platform

from ..utils import get_logger
from . import omit
from .gateway import GatewayOperationDispatcher, GatewayOperation


_LOG = get_logger('discooord')


# Dispatch (0) is a special case located in the gateway module


@GatewayOperationDispatcher.register(2)
class Identify(GatewayOperation):
    spec = {
        'token': str,
        'properties': None,  # TODO?
        'compress': bool,
        'large_threshold': int,
        'shard': [int]
    }


@GatewayOperationDispatcher.register(3)
class Status(GatewayOperation):
    spec = {
        'idle_since': int,
        'game': {'name':  str}
    }


@GatewayOperationDispatcher.register(6)
class Resume(GatewayOperation):
    spec = {
        'token': str,
        'session_id': str,
        'seq': int
    }


@GatewayOperationDispatcher.register(9)
class InvalidSession(GatewayOperation):
    spec = {}

    def handle(self, client):
        # Identity
        # TODO: Config system
        # TODO: Abstract (InvalidSession and Hello use this same block)
        client.send(Identify(
            token=client.token,
            properties={
                '$os': platform.system(),
                '$browser': 'discooord',
                '$device': 'discooord',
                '$referrer': '',
                '$referring_domain': ''
            },
            compress=False,
            large_threshold=250,
            shard=omit  # TODO: Actual model spec...
        ))


@GatewayOperationDispatcher.register(10)
class Hello(GatewayOperation):
    spec = {
        'heartbeat_interval': int,
        '_trace': [str]
    }

    def handle(self, client):
        # Start heartbeat
        client.start_heartbeat_timer(interval=self.heartbeat_interval / 1000.0)

        if not client.session_id:
            # Identity
            # TODO: Config system
            # TODO: Abstract
            client.send(Identify(
                token=client.token,
                properties={
                    '$os': platform.system(),
                    '$browser': 'discooord',
                    '$device': 'discooord',
                    '$referrer': '',
                    '$referring_domain': ''
                },
                compress=False,
                large_threshold=250,
                shard=omit  # TODO: Actual model spec...
            ))
        else:
            client.send(Resume(
                token=client.token,
                session_id=client.session_id,
                seq=client.last_sequence
            ))


@GatewayOperationDispatcher.register(11)
class HeartbeatACK(GatewayOperation):
    def handle(self, client):
        _LOG.debug('Heartbeat ACK')
