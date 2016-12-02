from tornado import gen
from tornado.httpclient import AsyncHTTPClient, HTTPClient, HTTPRequest
from aws_sign import ServiceConstants
from aws_sign.v4.auth import Authorization
from aws_sign.v4.canonical import ArgumentBuilder
from datetime import datetime
from copy import deepcopy

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
def _merge(source, overrides):
    for ok, ov in overrides.iteritems():
        if ok in source:
            if type(ov) == type(source[ok]):
                if type(ov) == dict:
                    _merge(source[ok], ov)
                else:
                    source[ok] = ov
            else:
                raise Exception("Mismatched types for key=%s: src=%s ov=%s" % (ok, type(source[ok]), type(ov)))
        else:
            source[ok] = ov
    return source


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
                   'headers': self._merge({'x-amz-date': amzdate}, headers),
                   'payload': payload if payload else ''
                 }
        return { 'x-amz-date': amzdate, 'Authorization': self.auth.header(**kwargs) }
    
  
class HTTP(object):
    """Base HTTP client
    
    Contains interfaces necessary for AWS signature signing support.  Subclasses should mixin
    behavior for signature support.
    """
    def __init__(self, client, constants, defaults=None, logger=None):
        """ Initialize instance with tornado client implemenation
        
        Parameters:
            client: Tornado HTTP client
            constants: ServiceConstants object
            defaults: keyword dict of default HTTPRequest parameters
            logger: logger
        """
        self.client    = client
        self.constants = constants
        self.defaults  = defaults
        self.logger    = logger if logger else _get_logger()

    def _merge(self, base, overrides):
        """
        Applies overrides to base dict
         
        Parameters:
            base: base dict 
            overrides: applies overrides to base dict, if provided

        Returns dict
        """
        return _merge(deepcopy(base), overrides) if overrides else base

    def _path(self, path):
        return path if path[0] == '/' else '/%s' % path

    def _url(self, path, qs):
        return self.constants.url + path + ('?%s' % qs if qs else '')

    def _log_request(self, params):
        self.logger.debug('HTTPRequest')
        self.logger.debug('-----------')
        for k, v in params.iteritems():
            self.logger.debug('%s=%s' % (k.upper(), v))
    
    def sign(self, path, method, headers, qs, payload):
        """Implements signing algorithm
        
        Subclasses should override this method with a specific signing
        implementation.

        Parameters:
            path: uri
            method: HTTP method
            headers: HTTP headers
            qs: urlencoded querystring 
            payload: HTTP request body
            
        Returns signed HTTP headers
        """
        self.logger.debug('Default signing')
        return headers

    def prepare_args(self, method, path, query_args=None, headers=None, payload=None):
        """Preformats arguments for request 
        
        Parameters:
            method: HTTP method
            path: uri
            headers: HTTP headers
            query_args: query arguments dict
            payload: HTTP payload

        Returns dict of prepped arguments
        """
        headers = headers if headers else {}
        qs      = ArgumentBuilder.canonical_query_string(query_args)
        path    = self._path(path)
        url     = self._url(path, qs)
        headers = self._merge(self.sign(path, method, headers, qs, payload), headers)        
        kwargs  = self._merge(self.defaults, {'url': url, 'method': method, 'headers': headers, 'body': payload})
        
        self._log_request(kwargs)
        return kwargs

    def request(self, method, path, headers=None, query_args=None, payload=None):
        """Disptach HTTP request """
        kwargs = self.prepare_args(method, path, query_args, headers, payload)
        return self.client.fetch(HTTPRequest(**kwargs))

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
    def __init__(self, constants, impl='curl', defaults=None, logger=None):
        AsyncHTTPClient.configure(TORNADO_IMPL[impl])
        super(SyncHTTP, self).__init__(HTTPClient(), constants, defaults, logger)


class AsyncHTTP(HTTP):
    def __init__(self, constants, impl='curl', defaults=None, logger=None):
        AsyncHTTPClient.configure(TORNADO_IMPL[impl])
        super(AsyncHTTP, self).__init__(AsyncHTTPClient(), constants, defaults, logger)

    @gen.coroutine
    def request(self, method, path, headers=None, query_args=None, payload=None):
        kwargs = self.prepare_args(method, path, query_args, headers, payload)
        resp = yield self.client.fetch(HTTPRequest(**kwargs))
        raise gen.Return(resp)
    
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

def get_instance(endpoint, constants_cls=None, creds=None, async=False, sign=True, defaults=None):
    """Create HTTPClient instance
    
    An HTTPClient instance is dynamically assembled based on ``async`` and ``sign``
    parameters.  A v4 signature authorizer is mixed in if signing is required.

    Parameters:
        endpoint: url endpoint
        constants_cls: ServiceConstants factory class
        creds: AWS Credentials
        async: bool that determines if underlying client is async or sync
        sign: bool that determines if requests are signed
        defaults: keyword dict of default HTTPRequest parameters 
       
    Returns HTTPClient instance
    """
    if sign and creds is None:
        raise Exception("AWS Credentials required for signing.")
    
    if constants_cls:
        constants = constants_cls.from_url(endpoint)

    defaults = defaults if defaults else {}
    base     = _get_base_cls(async, sign)
    attrs    = {'auth': Authorization(constants, creds)} if sign else {}
    return type('HTTPClient', base, attrs)(constants, defaults=defaults)



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
            pprint.pprint(json.loads(fetch(*args).body.decode('utf-8')))
        except HTTPError, e:
            print e.response.body
        except Exception, e:
            print e      

    @gen.coroutine
    def run_async(loop, fetch, *args):
        try:
            resp = yield fetch(*args)
            pprint.pprint(json.loads(resp.body.decode('utf-8')))
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
    endpoint = None
    http_test = os.environ.get('AWS_SIGN_HTTP_TEST', None)
    if http_test:
        env      = json.loads(http_test)
        endpoint = env.get('endpoint', None)
        path     = env.get('path', '/')
        defaults = env.get('defaults', {})
        
    if not endpoint:
        raise Exception("Please specify an API endpoint")

    creds = session.Session().get_credentials()
    if not creds:
        raise Exception("Unknown credentials")
    
    #
    # Example 1 - async run
    #

    # signed request
    print "ASYNC RUN"
    client = get_instance(endpoint, APIGatewayServiceConstants, creds, async=True, sign=True, defaults=defaults)

    loop = ioloop.IOLoop.current()
    loop.spawn_callback(lambda: run_async(loop, client.get, path))
    loop.start()

    #
    # Example 2 - sync run
    #

    # signed request
    print "SYNC RUN - signed"
    client = get_instance(endpoint, APIGatewayServiceConstants, creds, async=False, sign=True, defaults=defaults)
    run(client.get, path)
    
    # unsigned request
    print "SYNC RUN - unsigned"
    client = get_instance(endpoint, APIGatewayServiceConstants, creds, async=False, sign=False, defaults=defaults)
    run(client.get, path)
