import json
import logging
import urllib3
import urllib3.util
from urllib.parse import urlencode
import certifi


logger = logging.getLogger()

retry = urllib3.Retry(total = 3, backoff_factor=0.5)
timeout = urllib3.util.timeout.Timeout(connect=60.0, read=60.0)

def do_request(method, endpoint, **kwargs):
    http = urllib3.PoolManager(
        retries = retry, 
        timeout=timeout,
        cert_reqs='CERT_REQUIRED',
        ca_certs=certifi.where()
    )

    if method == 'GET' and 'params' in kwargs:
        params = kwargs.get('params')
        endpoint = endpoint + ("?" + urlencode(params) if params is not None else "")

    req_params = {}

    if 'headers' in kwargs:
        req_params['headers'] = kwargs.get('headers')

    if method in ['POST','PUT']:
        if 'json' in kwargs:
            req_params['body'] = json.dumps(kwargs.get('json'))
        elif 'data' in kwargs:
            req_params['body'] = kwargs.get('data')
    try:
        raw_response = http.urlopen(method, endpoint, **req_params)
        res = HttpResponse(raw_response)

        if res.status_code < 200 or res.status_code >= 300:
            logger.info(endpoint)
            logger.info(res.status_code)
            logger.info(res.text)
        
        return res
    except Exception as e:
        logger.error(endpoint)
        logger.error(e)
        return HttpResponse(None)

def get(endpoint, **kwargs):
    return do_request('GET', endpoint, **kwargs)

def post(endpoint, **kwargs):
    return do_request('POST', endpoint, **kwargs)

def put(endpoint, **kwargs):
    return do_request('PUT', endpoint, **kwargs)
    
class HttpResponse:
    def __init__(self, response):
        self.status_code = None
        try:
            self._response = response
            self.data = response.data
            self.status_code = response.status
            self.text = response.data.decode('utf-8')
        except Exception as e:
            self.text = str(response.data) if response is not None else None
            logger.info(e)

    def json(self):
        try:
            return json.loads(self.text)
        except Exception as e:
            logger.info(e)
            return None