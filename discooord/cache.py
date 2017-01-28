from collections import defaultdict
from functools import partial

from .exceptions import DiscordError
from .enums import *


# TODO: Implement usage
# TODO: Add "extras" to model that are not part of the base object to store relationships?


class Cache(object):
    '''Keeps track of the state for the client. Adds event handlers to keep state updated.'''
    client = None

    # Map of id to object
    guilds = None
    channels = None
    users = None
    emojis = None

    # Map of owner id to object list
    #guild_channels = None
    #guild_users = None

    def __init__(self, client):
        self.client = client

        self.guilds = {}
        self.channels = {}
        #self.guild_channels = defaultdict(dict)
        self.users = {}
        self.guild_memberships = defaultdict(dict)
        self.emojis = {}

        self.client.register_event_listener(EVENT_READY, self.on_ready)
        self.client.register_event_listener(EVENT_GUILD_CREATE, self.on_guild_create)
        self.client.register_event_listener(EVENT_GUILD_UPDATE, partial(self.on_update, self.guilds))
        self.client.register_event_listener(EVENT_GUILD_DELETE, self.on_guild_delete)
        self.client.register_event_listener(EVENT_GUILD_EMOJIS_UPDATE, self.on_guild_emojis_update)

    # Generic handlers for simple changes to state (Delete is too proprietary to the payloads involved)
    def on_create(self, cache, client, payload):
        cache[payload.id] = payload

    def on_update(self, cache, client, payload):
        if payload.id not in cache:
            raise DiscordError('Cache update triggered for unknown payload.id')
        cache[payload.id].merge(payload)

    # Gateway connection ready
    def on_ready(self, client, payload):
        for channel in payload.private_channels:
            self.channels[channel.id] = channel

    # Guild
    def on_guild_create(self, client, payload):
        self.guilds[payload.id] = payload

        for member in payload.members:
            self.users[member.user.id] = member.user
            self.guild_memberships[payload.id][member.user.id] = member

        for channel in payload.channels:
            channel.guild_id = payload.id
            self.channels[channel.id] = channel
            #self.guild_channels[payload.id][channel.id] = channel

        for emoji in payload.emojis:
            #emoji.guild_id = payload.id
            self.emojis[emoji.id] = emoji

    def on_guild_emojis_update(self, client, payload):
        if payload.guild_id not in self.guilds:
            raise DiscordError('Guild emoji update triggered for unknown guild_id ({})'.format(payload.guild_id))
        self.guilds[payload.guild_id].emojis = payload.emojis

    def on_guild_delete(self, client, payload):
        if payload.id not in self.guilds:
            raise DiscordError('Guild delete triggered for unknown id ({})'.format(payload.id))
        self.guilds.pop(payload.id)
