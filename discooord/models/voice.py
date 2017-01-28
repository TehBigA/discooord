from . import Model, snowflake


class VoiceState(Model):
    spec = {
        'guild_id': snowflake,
        'channel_id': snowflake,
        'user_id': snowflake,
        'session_id': str,
        'deaf': bool,
        'mute': bool,
        'self_deaf': bool,
        'self_mute': bool,
        'suppress': bool
    }


class VoiceRegion(Model):
    spec = {
        'id': snowflake,
        'name': str,
        'sample_hostname': str,
        'sample_port': int,
        'vip': bool,
        'optimal': bool
    }
