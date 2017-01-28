from ..utils import get_logger

from .gateway import GatewayEventDispatcher, GatewayEvent

from . import snowflake
from .guild import Guild, GuildMember
from .user import User, Presence
from .chat import DMChannel, Message, Reaction, TypingStart, Emoji
from .operations import Status
from .voice import VoiceState


_LOG = get_logger('discooord')


@GatewayEventDispatcher.register()
class Ready(GatewayEvent):
    spec = {
        'v': int,
        'user': object,
        'private_channels': [DMChannel],
        'guilds': [Guild],
        'session_id': str,
        'presences': [None],  # TODO: N/A to Bots
        'relationships': [None],  # TODO: N/A to Bots
        '_trace': [str]
    }

    def handle(self, client):
        super(Ready, self).handle(client)

        _LOG.info('READY event received')

        client.session_id = self.session_id
        client.send(Status(idle_since=None, game={'name': 'Discord API Client Development'}))


@GatewayEventDispatcher.register()
class Resumed(GatewayEvent):
    spec = {
        '_trace': [unicode]
    }

    def handle(self, client):
        super(Resumed, self).handle(client)

        _LOG.info('RESUMED event received')

        client.send(Status(idle_since=None, game={'name': 'Discord API Client Development'}))


@GatewayEventDispatcher.register()
class GuildCreate(GatewayEvent, Guild):
    pass


@GatewayEventDispatcher.register()
class GuildUpdate(GatewayEvent, Guild):
    pass


@GatewayEventDispatcher.register()
class GuildDelete(GatewayEvent):
    spec = {
        'id': snowflake,
        'unavailable': bool
    }


@GatewayEventDispatcher.register()
class GuildEmojisUpdate(GatewayEvent):
    spec = {
        'guild_id': snowflake,
        'emojis': [Emoji]
    }


@GatewayEventDispatcher.register()
class GuildMemberAdd(GatewayEvent, GuildMember):
    spec = {
        'guild_id': snowflake
    }


@GatewayEventDispatcher.register()
class GuildMemberRemove(GatewayEvent):
    spec = {
        'guild_id': snowflake,
        'user': User
    }


@GatewayEventDispatcher.register()
class GuildMemberUpdate(GatewayEvent):
    spec = {
        'guild_id': snowflake,
        'roles': [snowflake],
        'user': User,
        'nick': unicode
    }


@GatewayEventDispatcher.register()
class MessageCreate(GatewayEvent, Message):
    pass


@GatewayEventDispatcher.register()
class MessageReactionAdd(GatewayEvent, Reaction):
    pass


@GatewayEventDispatcher.register()
class MessageReactionRemove(GatewayEvent, Reaction):
    pass


@GatewayEventDispatcher.register()
class TypingStart(GatewayEvent, TypingStart):
    pass


@GatewayEventDispatcher.register()
class PresenceUpdate(GatewayEvent, Presence):
    pass


@GatewayEventDispatcher.register()
class VoiceStateUpdate(GatewayEvent, VoiceState):
    pass
