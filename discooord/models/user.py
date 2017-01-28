from . import Model, snowflake, long


class User(Model):
    spec = {
        'id': snowflake,
        'username': str,
        'discriminator': str,
        'avatar': str,
        'bot': bool,
        'mfa_enabled': bool,
        'verified': bool,
        'email': str
    }


class UserGuild(Model):
    spec = {
        'id': snowflake,
        'name': str,
        'icon': str,
        'owner': bool,
        'permissions': long
    }


class Presence(Model):
    spec = {
        'user': User,
        'roles': [snowflake],
        'game': dict,
        'nick': str,
        'guild_id': snowflake,
        'status': str
    }
