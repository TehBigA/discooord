from . import Model, snowflake
from ..utils import parse_datetime

from .user import User


class IntegrationAccount(Model):
    spec = {
        'id': str,
        'name': str
    }


class Integration(Model):
    spec = {
        'id': snowflake,
        'name': str,
        'type': str,
        'enabled': bool,
        'syncing': bool,
        'role_id': snowflake,
        'expire_behavior': int,
        'expire_grace_period': int,
        'user': User,
        'account': IntegrationAccount,
        'synced_at': parse_datetime
    }
