from . import Model, snowflake, long
from .base import User


class ApplicationInfo(Model):
    spec = {
        'id': snowflake,
        'name': str,
        'description': str,
        'icon': str,
        'flags': long,
        'rpc_origins': [str],
        'owner': User
    }
