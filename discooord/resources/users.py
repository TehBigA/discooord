from . import Resource
from ..models.user import User, UserGuild
from ..models.chat import DMChannel


class Users(Resource):
    def query(self, q, limit=25):
        url = self.build_url()
        data = self.client._make_request(url, params={
            'q': q,
            'limit': limit
        })
        return [User(row) for row in data]

    def get(self, primary='@me'):
        url = self.build_url(primary)
        data = self.client._make_request(url)
        return User(data)

    def guilds(self, primary='@me'):
        url = self.build_url(primary, 'guilds')
        data = self.client._make_request(url)
        return [UserGuild(d) for d in data]

    def create_dm(self, recipient, primary='@me'):
        url = self.build_url(primary, 'channels')

        response = self.client._make_request(url, data={
            'recipient_id': recipient if isinstance(recipient, str) else recipient.id
        }, method='POST')

        return DMChannel(response)
