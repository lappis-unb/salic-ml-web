import requests

BASE_URL = "http://www.mocky.io"

class HttpFinancialMetrics:
    def __init__(self, base_url):
        self.base_url = base_url

    def request_json(self, endpoint):
        response = requests.get(self.base_url + endpoint)
        json = response.json()
        return json

    def number_of_items(self, pronac):
        endpoint = "/v2/5bba5c823100007400148c5b"
        response = self.request_json(endpoint)
        return response

http_financial_metrics_instance = HttpFinancialMetrics(BASE_URL)
