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



class HTTP(object):
    """HTTP Client with built-in AWS Signature version 4 support.
    
    HTTP requests are encoded with AWS signing signature required for secure API access.
    """
    def __init__(self, creds, endpoint, impl='curl', svc_cons_cls=ServiceConstants, logger=None):
        """ Initialize instance with tornado client implemenation
        
        Parameters:
            creds: aws credentials
            endpoint: aws service enpoint
            impl: tornado client implemenation
            svc_cons_cls: ServiceConstants class
        """
        AsyncHTTPClient.configure(TORNADO_IMPL[impl])
        self.client = HTTPClient()
        self.cons   = svc_cons_cls.from_url(endpoint)
        self.auth   = Authorization(self.cons, creds)
        self.logger = logger if logger else _get_logger()

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
    
    def sign(self, path, method, headers=None, qs='', payload=''):
        """Generate request authoriazation
        
        Parameters:
            path: uri
            query_args: query args dict
            
        Returns request signing headers
        """
        now     = datetime.utcnow()
        amzdate = self._amzdate(now)
        dtstamp = self._datestamp(now)

        # Generate 'Authorization' header for signing request
        self.logger.debug('Signing Request...')
        self.logger.debug('AMZDATE=%s' % amzdate)
        self.logger.debug('DSTAMP=%s' % dtstamp)
        self.logger.debug('METHOD=%s' % method)
        self.logger.debug('PATH=%s' % path)
        self.logger.debug('QS=%s' % qs)

        auth_header = self.auth.header(amzdate, dtstamp, path, method, qs,
                                       _merge({'x-amz-date':amzdate}, headers), payload)
        self.logger.debug(auth_header)

        # Set HTTP headers for request
        return _merge({'x-amz-date':amzdate, 'Authorization': auth_header}, headers)

    def get(self, path, headers=None, query_args=None):
        """ GET request

        Parameters:
            path: uri
            headers: HTTP headers

        Returns HTTP response object
        """
        qs      = ArgumentBuilder.canonical_query_string(query_args)
        url     = self.cons.url + path + ('?%s' % qs if qs else '')
        method  = 'GET'
        headers = self.sign(path, method, headers, qs)
        request = HTTPRequest(url, method, headers)
        
        self.logger.debug('URL=%s' % url)
        return self.client.fetch(request)
    
    def post(self, path, payload, headers=None, query_args=None):
        """ POST request
        
        Parameters:
            path: uri
            payload: request body
            headers: HTTP headers
            query_args: query args dict

        Returns HTTP response object
        """
        qs      = ArgumentBuilder.canonical_query_string(query_args)
        url     = self.cons.url + path + ('?%s' % qs if qs else '')
        method  = 'POST'
        headers = self.sign(path, method, headers, qs, payload)
        request = HTTPRequest(url, method, headers, body=payload)

        self.logger.debug('URL=%s' % url)
        return self.client.fetch(request)
