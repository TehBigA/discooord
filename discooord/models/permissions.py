from . import Model, snowflake


class Role(Model):
    spec = {
        'id': snowflake,
        'name': str,
        'color': int,
        'hoist': bool,
        'position': int,
        'permissions': int,
        'managed': bool,
        'mentionable': bool
    }
