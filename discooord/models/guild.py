from . import Model, snowflake
from ..utils import parse_datetime

from .chat import Emoji, Overwrite
from .permissions import Role
from .user import User, Presence
from .voice import VoiceState


class GuildMember(Model):
    spec = {
        'user': User,
        'nick': str,
        'roles': [Role],
        'joined_at': parse_datetime,
        'deaf': bool,
        'mute': bool
    }


class Channel(Model):
    spec = {
        'id': snowflake,
        'guild_id': snowflake,
        'name': str,
        'type': str,
        'position': int,
        'is_private': bool,
        'permission_overwrites': [Overwrite],
        'topic': str,
        'last_message_id': snowflake,
        'bitrate': int,
        'user_limit': int
    }


class Guild(Model):
    spec = {
        'id': snowflake,
        'name': str,
        'icon': str,
        'splash': str,
        'owner_id': snowflake,
        'region': str,
        'afk_channel_id': snowflake,
        'afk_timeout': int,
        'embed_enabled': bool,
        'embed_channel_id': snowflake,
        'verification_level': int,
        'default_message_notifications': int,
        'roles': [Role],
        'emojis': [Emoji],
        'features': [str],
        'mfa_level': int,
        'joined_at': parse_datetime,
        'large': bool,
        'unavailable': bool,
        'member_count': int,
        'voice_states': [VoiceState],
        'members': [GuildMember],
        'channels': [Channel],
        'presences': [Presence]
    }


class InviteMetadata(Model):
    spec = {
        'inviter': User,
        'uses': int,
        'max_uses': int,
        'max_age': int,
        'temporary': bool,
        'created_at': parse_datetime,
        'revoked': bool,
    }


class InviteGuild(Model):
    spec = {
        'id': snowflake,
        'name': str,
        'splash_hash': str,
    }


class InviteChannel(Model):
    spec = {
        'id': snowflake,
        'name': str,
        'type': str,
    }


class Invite(Model):
    spec = {
        'code': str,
        'guild': InviteGuild,
        'channel': InviteChannel,
    }
