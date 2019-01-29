import requests
import json


class RestClient:
    def __init__(self, base_uri):
        self.base_uri = base_uri

    def request(self, endpoint, params=[]):
        request_url = self.base_uri + endpoint
        if len(params) > 0:
            i = 0
            for key in params:
                if i == 0:
                    request_url += "?" + str(key) + "=" + str(params[key])
                else:
                    request_url += "&" + str(key) + "=" + str(params[key])
                i += 1

        response = requests.get(request_url, verify=True)
        if response.ok:
            j_data = json.loads(response.content)
            return j_data
        else:
            raise Exception('Error in REST request.')
