from getenv import env
import drest

class MetpetAPI():
    def __init__(self, user, api):
        self.username = user
        self.api_key = api
        self.api = drest.api.TastyPieAPI(env('API_DRF_HOST'))
        if self.username:
            self.api.auth(user, api)
