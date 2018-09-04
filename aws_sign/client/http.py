import six
from tornado import gen
from tornado.httpclient import AsyncHTTPClient, HTTPClient, HTTPRequest

from aws_sign import ServiceConstants
from aws_sign.v4.auth import Authorization
from aws_sign.v4.canonical import ArgumentBuilder

from datetime import datetime
from copy import deepcopy

import re
import logging

#
# Constants
#
TORNADO_IMPL = {
    'curl':   'tornado.curl_httpclient.CurlAsyncHTTPClient',
    'simple': 'tornado.simple_httpclient.SimpleAsyncHTTPClient'
}

#
# Utils
#
def _get_logger(name='aws_sign.http'):
    return logging.getLogger(name)

def _lower(source, acc):
    """Set all dict keys to lowercase format."""
    for k, v in six.iteritems(source):
        acc[k.lower()] = _lower(v, {}) if type(v) is dict else v
    return acc

def _normalize(source):
    """Creates a uniform format for dict keys."""
    return _lower(source, {})

def _merge(source, overrides):
    """Deep merge of dicts."""
    for ok, ov in six.iteritems(overrides):
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


class UnknownCredentialsException(Exception):
    def __init__(self):
        super(UnknownCredentialsException, self).__init__("AWS Credentials are required for signing.")

class DefaultServiceConstants(ServiceConstants):
    URL_REGEX = re.compile(r"""^(http[s]?)://  # scheme
                                ([\w\-\.]+)    # endpoint
                                ([:][\d]+)?$   # port""", re.X)    

    FORMAT = 'http[s]?://[\w\-\.](?:[:][\d]+)'

    def __init__(self, scheme, host, port=None):
        self.scheme = scheme
        self.host = host
        self.port = int(port[1:]) if port else port

    @property
    def url(self):
        url = super(DefaultServiceConstants, self).url
        if self.port:
            url += ':%d' % self.port
        return url

    def __str__(self):
        return 'scheme=%s\nhost=%s\nport=%s' % (self.scheme, self.host, self.port)


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
        """Generate all headers required for signed request
        
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
        amz_hdr = {'x-amz-date': amzdate}
        return self._merge(amz_hdr, 
                           self.auth.headers(amzdate=amzdate,
                                             datestamp=self._datestamp(now),
                                             uri=path,
                                             method=method,
                                             qs=qs,
                                             headers=self._merge(amz_hdr, headers),
                                             payload=payload if payload else ''))
    
  
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
        for k, v in six.iteritems(params):
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

        # Like headers can vary due to case insensitivity so we must normalize names for proper merging 
        # between defaults and input headers.
        if 'headers' in self.defaults:
            self.defaults['headers'] = _normalize(self.defaults['headers'])

        qs      = ArgumentBuilder.canonical_query_string(query_args)
        path    = self._path(path)
        url     = self._url(path, qs)
        headers = self._merge(self.sign(path, method, headers, qs, payload), headers)        
        kwargs  = self._merge(self.defaults, {'url': url, 'method': method, 'headers': _normalize(headers), 'body': payload})
        
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


def _get_base_cls(asynch=False, sign=True):
    impl = (AsyncHTTP,) if asynch else (SyncHTTP,)
    return (AuthMixin,) + impl if sign else impl 

def get_instance(endpoint, constants_cls=DefaultServiceConstants, defaults=None, 
                 asynch=True, sign=False, creds=None, logger=None):
    """Create HTTPClient instance
    
    An HTTPClient instance is dynamically assembled based on ``asynch`` and ``sign``
    parameters.  A v4 signature authorizer is mixed in if signing is required.

    Parameters:
        endpoint: service endpoint
        constants_cls: ServiceConstants factory class
        defaults: keyword dict of default HTTPRequest parameters 
        asynch: bool that determines if underlying client is asynchronous or synchronous
        sign: bool that determines if requests are signed
        creds: AWS Credentials
       
    Returns HTTPClient instance
    """
    if sign and creds is None:
        raise UnknownCredentialsException()
    
    constants = constants_cls.from_url(endpoint)

    defaults = defaults if defaults else {}
    base     = _get_base_cls(asynch, sign)
    attrs    = {'auth': Authorization(constants, creds)} if sign else {}
    return type('HTTPClient', base, attrs)(constants, defaults=defaults, logger=logger)
