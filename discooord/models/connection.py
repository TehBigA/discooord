from . import Model, snowflake

from .integration import Integration


class Connection(Model):
    spec = {
        'id': snowflake,
        'name': str,
        'type': str,
        'revoked': bool,
        'integrations': [Integration]
    }
