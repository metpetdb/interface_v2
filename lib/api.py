from getenv import env
import drest

class MetpetAPI():
    def __init__(self, user, api):
        self.username = user
        self.api_key = api
        self.api = drest.api.TastyPieAPI('{0}/api/v1/'.format(env('API_HOST_DRF')))
        if self.username:
            self.api.auth(user, api)
