from tornado import gen
from tornado.httpclient import AsyncHTTPClient, HTTPClient, HTTPRequest
from datetime import datetime
from aws_sign import ServiceConstants
from aws_sign.v4.auth import Authorization
from aws_sign.v4.canonical import ArgumentBuilder

import re
import logging
import logging.config


#
# Constants
#
TORNADO_IMPL = {
    'curl':   'tornado.curl_httpclient.CurlAsyncHTTPClient',
    'simple': 'tornado.simple_httpclient.SimpleAsyncHTTPClient'
}

#
# Configure Logging
#
logging_config = dict(
    version = 1,
    formatters = {
        'f': {'format':
              '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'}
        },
    
    handlers = {
        'h': {'class': 'logging.StreamHandler',
              'formatter': 'f',
              'level': logging.DEBUG}
        },

    root = {
        'handlers': ['h'],
        'level': logging.INFO,
        },
    
    loggers = {
        'aws_sign.http': {
            'handlers': ['h'],
            'level': logging.DEBUG,
            'propagate': False
            },
        }  
    )
logging.config.dictConfig(logging_config)

def _get_logger(name='aws_sign.http'):
    return logging.getLogger(name)

#
# Utils
#
def _merge(required, optional=None):
    """Merges dict

    Merges base dict with optional dict if possible

    Parameters:
        required: dict
        optional: dict
    Returns dict
    """
    return dict(optional, **required) if optional else required


class AuthMixin(object):
    def _amzdate(self, dt):
        """Convert datetime into Amazon timestamp format
        
        Parameter:
            dt: datetime
            
        Returns timestamp string
        """
        return dt.strftime('%Y%m%dT%H%M%SZ')

    def _datestamp(self, dt):
        """Convert datetime into Amazon date format
        
        Parameters:
            dt: datetime

        Returns date string
        """
        return dt.strftime('%Y%m%d')
    
    def sign(self, path, method, headers=None, qs='', payload=None):
        """Generate request authoriazation
        
        Parameters:
            path: uri
            method: HTTP method
            headers: HTTP headers
            qs: url querystring
            payload: HTTP payload
            
        Returns request signing headers
        """
        now     = datetime.utcnow()
        amzdate = self._amzdate(now)
        
        kwargs = { 'amzdate': amzdate,
                   'datestamp': self._datestamp(now),
                   'uri': path,
                   'method': method,
                   'qs': qs,
                   'headers': _merge({'x-amz-date': amzdate}, headers),
                   'payload': payload if payload else ''
                 }
        return { 'x-amz-date': amzdate, 'Authorization': self.auth.header(**kwargs) }
    
  
class HTTP(object):
    """Base HTTP client
    
    Contains interfaces necessary for AWS signature signing support.  Subclasses should mixin
    behavior for signature support.
    """
    def __init__(self, client, constants, logger=None):
        """ Initialize instance with tornado client implemenation
        
        Parameters:
            client: Tornado HTTP client
            constants: ServiceConstants object
            logger: logger
        """
        self.client    = client
        self.constants = constants 
        self.logger    = logger if logger else _get_logger()

    def sign(self, path, method, headers, qs, payload):
        """Implement """
        self.logger.debug('Default signing')
        return headers

    def prepare_args(self, path, method, query_args=None, headers=None, payload=None):
        """Preformats arguments for request 
        
        Parameters:
            path: uri
            headers: HTTP headers
            query_args: query arguments dict
            payload: HTTP payload

        Returns tuple of prepped arguments
        """
        path    = path if path[0] == '/' else '/%s' % path
        qs      = ArgumentBuilder.canonical_query_string(query_args)
        url     = self.constants.url + path + ('?%s' % qs if qs else '')
        headers = _merge(self.sign(path, method, headers, qs, payload), headers)        

        self.logger.debug('URL=%s' % url)
        self.logger.debug('HEADERS=%s' % headers)
        return (url, headers)

    def request(self, method, path, headers=None, query_args=None, payload=None):
        """Disptach HTTP request """
        url, headers = self.prepare_args(path, method, query_args, headers, payload)
        return self.client.fetch(HTTPRequest(url, method, headers, body=payload)).body

    def get(self, path, headers=None, query_args=None):
        """ GET request

        Parameters:
            path: uri
            headers: HTTP headers
            query_args: query arguments dict
            kwargs: passthru keyword arguments for HTTPRequest

        Returns HTTP response object
        """
        return self.request('GET', path, headers, query_args)
    
    def post(self, path, payload, headers=None, query_args=None):
        """ POST request
        
        Parameters:
            path: uri
            payload: request body
            headers: HTTP headers
            query_args: query arguments dict
            kwargs: passthru keywargs arguments for HTTPRequest

        Returns HTTP response object
        """
        return self.request('POST', path, headers, query_args, payload)


class SyncHTTP(HTTP):
    def __init__(self, constants, impl='curl', logger=None):
        AsyncHTTPClient.configure(TORNADO_IMPL[impl])
        super(SyncHTTP, self).__init__(HTTPClient(), constants, logger)


class AsyncHTTP(HTTP):
    def __init__(self, constants, impl='curl', logger=None, http_defaults=None):
        AsyncHTTPClient.configure(TORNADO_IMPL[impl])
        super(AsyncHTTP, self).__init__(AsyncHTTPClient(defaults=http_defaults), constants, logger)

    @gen.coroutine
    def request(self, method, path, headers=None, query_args=None, payload=None):
        url, headers = self.prepare_args(path, method, query_args, headers, payload)
        resp = yield self.client.fetch(HTTPRequest(url, method, headers, body=payload))
        raise gen.Return(resp.body)
    
    @gen.coroutine
    def get(self, path, headers=None, query_args=None):
        resp = yield self.request('GET', path, headers, query_args)
        raise gen.Return(resp)
    
    @gen.coroutine
    def post(self, path, payload, headers=None, query_args=None):
        resp = yield self.request('POST', path, headers, query_args, payload)
        raise gen.Return(resp)


def _get_base_cls(async=False, sign=True):
    impl = (AsyncHTTP,) if async else (SyncHTTP,)
    return (AuthMixin,) + impl if sign else impl 

def get_instance(endpoint, constants_cls=None, creds=None, async=False, sign=True):
    """Create HTTPClient instance
    
    An HTTPClient instance is dynamically assembled based on ``async`` and ``sign``
    parameters.  A v4 signature authorizer is mixed in if signing is required.

    Parameters:
        endpoint: url endpoint
        constants_cls: ServiceConstants factory class
        creds: AWS Credentials
        async: bool that determines if underlying client is async or sync
        sign: bool that determines if requests are signed
       
    Returns HTTPClient instance
    """
    if sign and creds is None:
        raise Exception("AWS Credentials required for signing.")
    
    if constants_cls:
        constants = constants_cls.from_url(endpoint)

    base  = _get_base_cls(async, sign)
    attrs = {'auth': Authorization(constants, creds)} if sign else {}
    return type('HTTPClient', base, attrs)(constants.from_url(endpoint))



#
#
# TESTING TESTING TESTING 
#
#

if __name__ == '__main__':
    #
    # TODO: Factor this out into examples subpackage.
    #

    from aws_sign.v4 import Sigv4ServiceConstants
    from tornado.httpclient import HTTPError
    from tornado import ioloop
    from boto3 import session

    import tornado.gen
    import pprint
    import json
    import re
    import os

    #
    # APIGateway interface 
    #
    class APIGatewayServiceConstants(Sigv4ServiceConstants):
        URL_REGEX = re.compile(r"""(?:https://)?   # scheme
                               (\w+            # api prefix
                               \.
                               ([\w\-]+)       # service
                               \.
                               ([\w\-]+)       # region
                               .amazonaws.com)
                               \/
                               ([\w]+)$        # stage""", re.X)
        
        def __init__(self, *args):
            super(APIGatewayServiceConstants, self).__init__(*args[:3])
            self.stage = args[3]

        def __str__(self):
            return 'host=%s\nservice=%s\nregion=%s\nstage=%s\nalgorithm=%s\nsigning=%s\nheaders=%s' % \
                (self.host, self.service, self.region, self.stage, self.algorithm, self.signing, self.headers)

    # END CLASS DEFINITION


    # HTTP client runners
    def run(fetch, *args):
        try:
            pprint.pprint(json.loads(fetch(*args)))
        except HTTPError, e:
            print e.response.body
        except Exception, e:
            print e      

    @gen.coroutine
    def run_async(loop, fetch, *args):
        try:
            resp = yield fetch(*args)
            pprint.pprint(json.loads(resp))
        except HTTPError, e:
            print e.response.body
        except Exception, e:
            print e      
        finally:
            loop.stop()

    #
    # MAIN 
    #

    # Parse arguments
    endpoint, path = None, None
    http_test = os.environ.get('AWS_SIGN_HTTP_TEST', None)
    if http_test:
        env      = json.loads(http_test)
        endpoint = env.get('endpoint', None)
        path     = env.get('path', '/')
        
    if not endpoint:
        raise Exception("Please specify an API endpoint")

    creds = session.Session().get_credentials()
    if not creds:
        raise Exception("Unknown credentials")
    
    # Example 1 - async run
    async_client = get_instance(endpoint, APIGatewayServiceConstants, creds, async=True, sign=True)

    loop = ioloop.IOLoop.current()
    loop.spawn_callback(lambda: run_async(loop, async_client.get, path))
    loop.start()

    # Example 2 - sync run
    sync_client = get_instance(endpoint, APIGatewayServiceConstants, creds, async=False, sign=True)
    run(lambda: sync_client.get(path))
    
    sync_noauth_client = get_instance(endpoint, APIGatewayServiceConstants, creds, async=False, sign=False)
    run(lambda: sync_noauth_client.get(path))
