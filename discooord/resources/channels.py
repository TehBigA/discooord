import random
import sys

from . import Resource, unicode
from ..enums import VALID_MESSAGE_POSITIONS
from ..models.guild import Channel
from ..models.chat import Message, DMChannel

from ..utils import untested


class Channels(Resource):
    @untested
    def get(self, channel_id):
        url = self.build_url(channel_id)
        response = self.client._make_request(url)
        return Channel(response)

    @untested
    def put(self, channel, name=None, position=None, topic=None, bitrate=None, user_limit=None):
        if not isinstance(channel, (Channel, str)):
            raise ValueError('channel')

        url = self.build_url(channel if isinstance(channel, str) else channel.id)

        response = self.client._make_request(url, data={
            'name': name,
            'position': position,
            'topic': topic,
            'bitrate': bitrate,
            'user_limit': user_limit
        }, method='PUT')

        return Channel(response)

    patch = put

    @untested
    def delete(self, channel, name=None, position=None, topic=None, bitrate=None, user_limit=None):
        if not isinstance(channel, (Channel, str)):
            raise ValueError('channel')

        url = self.build_url(channel if isinstance(channel, str) else channel.id)

        response = self.client._make_request(url, method='DELETE')

        return Channel(response)


class Messages(Resource):
    parent_resource = Channels

    @untested
    def all(self, channel, where=None, position=None, limit=50):
        if not isinstance(channel, (Channel, str)):
            raise ValueError('channel')
        elif (where is not None or position is not None):
            if position not in VALID_MESSAGE_POSITIONS:
                raise ValueError('position')
            elif where is None or not isinstance(where, (Message, str)):
                raise ValueError('where')

        url = self.build_url(channel if isinstance(channel, str) else channel.id)

        data = {
            'limit': limit
        }

        if where is not None:
            data[position] = where

        response = self.client._make_request(url, data=data, method='GET')

        return [Message(r) for r in response]

    def get(self, channel, message):
        if not isinstance(channel, (Channel, str)):
            raise ValueError('channel')
        elif not isinstance(message, (Message, str)):
            raise ValueError('message')

        url = self.build_url(
            channel if isinstance(channel, str) else channel.id,
            message if isinstance(message, str) else message.id
        )

        response = self.client._make_request(url, method='GET')

        return Message(response)

    def put(self, channel, content, tts=False):
        if not isinstance(channel, (Channel, DMChannel, str)):
            raise ValueError('channel')

        nonce = random.randint(-sys.maxint - 1, sys.maxint)

        url = self.build_url(channel if isinstance(channel, str) else channel.id)

        response = self.client._make_request(url, data={
            'content': unicode(content),
            'nonce': nonce,
            'tts': tts
        }, method='POST')

        return Message(response)

    def delete(self, channel, message):
        if not isinstance(channel, (Channel, str)):
            raise ValueError('channel')
        elif not isinstance(message, (Message, str)):
            raise ValueError('message')

        url = self.build_url(
            channel if isinstance(channel, str) else channel.id,
            message if isinstance(message, str) else message.id
        )

        self.client._make_request(url, method='DELETE')
