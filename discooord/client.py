from __future__ import print_function

from collections import defaultdict
import json
import requests
import socket
import time
import thread
import threading

#from concurrent import futures
from websocket import WebSocketApp, WebSocketConnectionClosedException

from .exceptions import ApiError, InvalidToken, GatewayError
from .enums import TOKEN_TYPE_BOT  # TODO: TOKEN_TYPE_BEARER
from .utils import get_logger, Timer

from .resources import *
from .cache import Cache
from .models import ModelEncoder
from .models.gateway import BuildablePayload, GatewayOperationDispatcher


ENDPOINT = 'https://discordapp.com/api'

_LOG = get_logger('discooord')
_WEBSOCKET_LOG = get_logger('websocket')
_GATEWAY_LOG = get_logger('discooord_gateway')


class Client(object):
    '''Discord client.'''

    reconnecting = False
    connection_lost = False
    shuttingdown = False

    reconnect_interval = 5

    resources = None
    event_listeners = None

    token_type = TOKEN_TYPE_BOT
    token = None

    request_endpoint = None
    request_session = None

    heartbeat = None
    #recovery_timer = None

    gateway_endpoint = None
    gateway_websocket = None
    runner = None

    log_gateway_messages = False

    identity = None
    session_id = None
    last_sequence = None

    cache = None

    def __init__(self, token=None, token_type=TOKEN_TYPE_BOT, request_endpoint=ENDPOINT, log_gateway_messages=False):
        self.heartbeat = Timer(self._send_heartbeat, background=False)
        #self.recovery_timer = Timer(self.connect, interval=5, background=False)

        self.token_type = token_type
        self.token = token
        self.request_endpoint = request_endpoint
        self.log_gateway_messages = log_gateway_messages

        # Start requests session
        self.request_session = requests.Session()

        self.event_listeners = defaultdict(list)

        self.cache = Cache(self)

        # Register available resources
        OAuth2.register(self)
        Gateway.register(self)
        Users.register(self)
        Channels.register(self)
        Messages.register(self)

    def shutdown(self):
        _LOG.info('Shutting down')

        self.shuttingdown = True
        self.reconnecting = False

        #self.recovery_timer.stop()

        if self.gateway_websocket:
            if not self.heartbeat.is_running() and self.gateway_websocket.sock:
                # Assume we started connecting to the gateway
                self.gateway_websocket.sock.abort()

            self.gateway_websocket.close()

        self.heartbeat.stop()
        self.runner.join()

        self.on_shutdown()

    def on_shutdown(self):
        pass

    def __enter__(self):
        self.authenticate(self.token, self.token_type)
        self.connect()
        return self

    def __exit__(self, type, value, traceback):
        return self.shutdown()

    def _make_request(self, url, data=None, params=None, method='GET'):
        try:
            response = self.request_session.request(
                url=self.request_endpoint + url,
                json=data,
                params=params,
                method=method
            )
        except requests.RequestException as e:
            _LOG.error('Unable to make request to api (Unknown error)', exc_info=True)
            raise e

        return self._parse_response(response)

    def _parse_response(self, response):
        try:
            response.raise_for_status()
            return response.json()
        except:
            # Non-200
            _LOG.error('Error returned from api', exc_info=True)
            raise ApiError(response=response)

    # Blocks during API call
    def authenticate(self, token=None, token_type=None):
        '''Caches token and fetches identity'''

        if self.identity is not None:
            return self.identity

        token_type = token_type or self.token_type
        token = token or self.token

        if self.token_type is None:
            raise ValueError('token_type')
        elif self.token is None:
            raise ValueError('token')
        elif token_type != TOKEN_TYPE_BOT:
            raise NotImplementedError()

        _LOG.info('Authenticating and fetching identity')

        self.request_session.headers['Authorization'] = '{} {}'.format(token_type, token)

        try:
            self.identity = self.oauth2.application()
            _LOG.info('Identity acquired ({}, {})'.format(self.identity.id, self.identity.name))
        except ApiError as e:
            if e.code in (401, 50014):
                _LOG.error('Unable to fetch identity (Token rejected)', exc_info=True)
                raise InvalidToken()
            raise e

        return self.identity

    def connect(self):
        '''Connects to the gateway and starts the event loop. Blocks while fetching gateway endpoint from REST API.'''

        if not self.token or not self.token_type or not self.identity:
            raise DiscordError('You must first provide a token and call `authenticate` before connecting')

        self.gateway_endpoint = self.gateway.get() if self.gateway_endpoint is None or self.reconnecting else self.gateway_endpoint

        _LOG.info('Connecting to gateway ({})'.format(self.gateway_endpoint))

        self.gateway_websocket = WebSocketApp(
            url=self.gateway_endpoint + '?v=5&encoding=json',
            on_message=self.on_message,
            on_open=self.on_connect,
            on_close=self.on_close,
            on_error=self.on_error
        )

        self.runner = threading.Thread(target=self._run)
        self.runner.start()

    def _run(self):
        while not self.shuttingdown:
            self.connection_lost = False

            try:
                self.gateway_websocket.run_forever()
            except socket.error as e:
                _LOG.error('Unable to connect to gateway ({})'.format(str(e)), exc_info=True)

                # If we couldn't make the connection the endpoint could be bad
                self.gateway_endpoint = None
            except Exception as e:
                _LOG.critical('Unknown gateway error in WebSocket.run_forever ({})'.format(str(e)), exc_info=True)

            if not self.shuttingdown:
                if self.connection_lost:
                    _LOG.info('Retrying connection in {} seconds due to unexpected connection loss'.format(self.reconnect_interval))

                time.sleep(self.reconnect_interval)

    def run(self, timeout=None):
        '''If not connected this will try to establish that otherwise it waits on the current connection'''

        if not self.runner or not self.runner.is_alive():
            self.connect()

        self.runner.join(timeout)

    def on_connect(self, websocket):
        _LOG.info('Connection to gateway established')

        self.reconnecting = False
        #self.recovery_timer.stop()

        # TODO: Lock in this class not in the websocket
        if not isinstance(self.gateway_websocket.sock.lock, thread.LockType):
            self.gateway_websocket.sock.lock = threading.Lock()

    def on_close(self, websocket):
        if not self.shuttingdown:
            self.connection_lost = True
            _LOG.error('Connection to gateway unexpectedly closed')
        else:
            _LOG.info('Connection to gateway closed')

        self.stop_heartbeat_timer()

        '''if not self.shuttingdown and not self.connection_lost:
            # Recover
            _LOG.info('Starting recovery timer')

            self.recovering = True
            self.recovery_timer.start()'''

    def on_error(self, websocket, e):
        _LOG.error('Gateway websocket exception ({})'.format(str(e)), exc_info=True)

        if isinstance(e, WebSocketConnectionClosedException):
            self.connection_lost = True

    def on_message(self, websocket, message):
        if self.log_gateway_messages:
            _GATEWAY_LOG.debug('Received message ({})'.format(str(message)))

        try:
            data = json.loads(message)

            dispatcher = GatewayOperationDispatcher(data)

            # Special case with events - set last sequence
            if dispatcher.op == 0:
                self.last_sequence = dispatcher.s

            dispatcher.dispatch(self)
        except ValueError:
            _LOG.error('Unable to parse gateway message as JSON ({})'.format(str(message)))
        except GatewayError as e:
            _LOG.error('Gateway exception ({})'.format(str(e.message)), exc_info=True)
        except Exception as e:
            _LOG.error('Unexpected gateway exception ({})'.format(str(e)), exc_info=True)

    def send(self, payload):
        if not isinstance(payload, BuildablePayload):
            raise ValueError('payload')

        message = json.dumps(payload.build(), cls=ModelEncoder)
        results = self.gateway_websocket.send(message)

        if self.log_gateway_messages:
            _GATEWAY_LOG.debug('Sending message ({})'.format(str(message)))
            _GATEWAY_LOG.debug('Message results ({})'.format(str(results)))

        return results

    def start_heartbeat_timer(self, interval):
        _LOG.info('Starting heartbeat timer ({} ms interval)'.format(interval * 1000.0))

        self.heartbeat.interval = interval
        self.heartbeat.start()

    def stop_heartbeat_timer(self):
        _LOG.info('Stopping heartbeat timer')

        self.heartbeat.stop()

    def _send_heartbeat(self):
        # TODO: Use payload object
        _LOG.debug('Sending heartbeat')
        self.gateway_websocket.send(json.dumps({
            'op': 1,
            'd': self.last_sequence
        }))

    def on_event(self, event, model):
        '''Triggers event listeneres'''

        for listener in self.event_listeners[event]:
            listener(self, model)

    def register_event_listener(self, event, fn):
        self.event_listeners[event].append(fn)

    def remove_event_listener(self, event, fn):
        self.event_listeners[event].remove(fn)

    def remove_event_listeners(self, event=None):
        if event is None:
            self.event_listeners = defaultdict(list)
        else:
            self.event_listeners[event] = list()

    def event(self, event):
        '''Decorator to register an event listener'''

        # Not sure this is good enough yet
        # TODO: assign a dict to this and remove `remove` when dict empty?

        def decorator(fn):
            def remove(client=None):
                client = client or self
                #client.event_listeners[event].remove(fn)
                client.remove_event_listener(event, fn)

            fn.remove = remove

            #self.event_listeners[event].append(fn)
            self.register_event_listener(event, fn)

            return fn

        return decorator
