from . import Model, snowflake, unicode
from ..utils import parse_datetime

from .user import User


class DMChannel(Model):
    spec = {
        'id': snowflake,
        'is_private': bool,
        'recipient': User,
        'last_message_id': snowflake
    }


class Overwrite(Model):
    spec = {
        'id': snowflake,
        'type': unicode,
        'allow': int,
        'deny': int
    }


class EmbedThumbnail(Model):
    spec = {
        'url': unicode,
        'proxy_url': unicode,
        'height': int,
        'width': int
    }


class EmbedProvider(Model):
    spec = {
        'name': unicode,
        'url': unicode
    }


class Embed(Model):
    spec = {
        'title': unicode,
        'type': unicode,
        'description': unicode,
        'url': unicode,
        'thumbnail': EmbedThumbnail,
        'provider': EmbedProvider
    }


class Attachment(Model):
    spec = {
        'id': snowflake,
        'filename': unicode,
        'size': int,
        'url': unicode,
        'proxy_url': unicode,
        'height': int,
        'width': int
    }


class Emoji(Model):
    spec = {
        'id': snowflake,
        'name': unicode,
        'roles': [],
        'require_colons': bool,
        'managed': bool
    }


class Reaction(Model):
    spec = {
        'channel_id': snowflake,
        'message_id': snowflake,
        'user_id': snowflake,
        'emoji': Emoji
    }


class Reactions(Model):
    spec = {
        'count': int,
        'me': bool,
        'emoji': Emoji
    }


class Message(Model):
    spec = {
        'id': snowflake,
        'channel_id': snowflake,
        'author': User,
        'content': unicode,
        'timestamp': parse_datetime,
        'edited_timestamp': parse_datetime,
        'tts': bool,
        'mention_everyone': bool,
        'mentions': [User],
        'mention_roles': [snowflake],  # Role IDs
        'attachments': [Attachment],
        'embeds': [Embed],
        'nonce': int,
        'pinned': bool,
        'reactions': [Reactions]
    }


class TypingStart(Model):
    spec = {
        'channel_id': snowflake,
        'user_id': snowflake,
        'timestamp': parse_datetime
    }
