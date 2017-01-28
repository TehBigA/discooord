from . import Resource
from ..models.oauth2 import ApplicationInfo


class OAuth2(Resource):
    def application(self, primary='@me'):
        url = self.build_url('applications', primary)
        data = self.client._make_request(url)
        return ApplicationInfo(data)
