from . import Resource


class Gateway(Resource):
    def get(self):
        url = self.build_url()
        data = self.client._make_request(url)
        return data['url']
