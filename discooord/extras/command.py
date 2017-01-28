from ..utils import get_logger
from ..enums import EVENT_MESSAGE_CREATE

from .utils import parse_argument_string


_LOG = get_logger('discooord')


class CommandManager(object):
    client = None

    registry = None

    trigger = '/'
    cleanup = False  # Remove message that triggered the executed command
    enabled = True
    help = True

    def __init__(self, client, trigger='/', cleanup=False, enabled=True, help=True):
        if client is None:
            raise ValueError('client')

        self.client = client
        self.client.register_event_listener(EVENT_MESSAGE_CREATE, self.on_message)

        self.trigger = trigger
        self.cleanup = cleanup
        self.registry = {}

        self.enabled = enabled

        if help:
            self.help = help
            self.register(Command(client, 'help', 'Triggers this help message.', target=self.help_target))

    def register(self, command):
        if isinstance(command, type) and issubclass(command, Command):
            command = command(self.client)
        self.registry[command.name] = command

    def on_message(self, client, message):
        if not self.enabled or message.author.id == self.client.identity.id or not message.content.startswith(self.trigger):
            return

        raw = message.content[len(self.trigger):]

        try:
            parsed = parse_argument_string(raw)
        except ValueError as e:
            _LOG.error('Argument parsing error ({})'.format(str(e)), exc_info=True)
            self.client.messages.put(message.channel_id, u"<@!{}> Couldn't understand your arguments ({}).".format(message.author.id, str(e)))
            return

        if len(parsed) == 0:
            return  # TODO: Return error?

        command = self.registry.get(parsed[0].lower(), None)
        if command is None:
            return  # TODO: Return error?

        try:
            command.execute(message, raw[len(command.name) + 1:], *parsed[1:])

            if self.cleanup or command.cleanup:
                self.client.messages.delete(message.channel_id, message.id)
        except:
            pass  # TODO

    def help_target(self, command, payload, raw, *args):
        message = u'\n'.join([u'{:10}{}'.format(k, u' - {}'.format(v.description) if v.description is not None else u'') for k, v in sorted(self.registry.iteritems()) if not v.hidden])
        self.client.messages.put(payload.channel_id, u"<@!{}> here is what I got:\n```{}\n{}```".format(payload.author.id, message, u'\n'.join(self.help) if isinstance(self.help, (tuple, list)) else ''))


class Command(object):
    client = None

    enabled = True
    name = None
    description = None
    cleanup = False
    hidden = False

    target = None

    def __init__(self, client, name=None, description=None, target=None, cleanup=None, hidden=None):
        if client is None:
            raise ValueError('client')

        self.client = client

        if name is not None:
            self.name = name.lower()
        else:
            self.name = self.__class__.__name__.lower()

        if description is not None:
            self.description = description

        if cleanup is not None:
            self.cleanup = cleanup

        if hidden is not None:
            self.hidden = hidden

        if target is not None:
            self.target = target

    def execute(self, payload, raw, *args):
        if self.target is None:
            return

        try:
            if hasattr(self.target, '__self__') and isinstance(self.target.__self__, Command):
                self.target(payload, raw, *args)
            else:
                self.target(self, payload, raw, *args)
        except Exception as e:
            _LOG.error('Unable to execute command function ({})'.format(str(e)), exc_info=True)
