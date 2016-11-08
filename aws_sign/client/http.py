from tornado.httpclient  import AsyncHTTPClient, HTTPClient, HTTPRequest
from datetime import datetime
from aws_sign import ServiceConstants
from aws_sign.v4 import Sigv4ServiceConstants
from aws_sign.v4 import auth

import re

TORNADO_IMPL = {
    'curl':   'tornado.curl_httpclient.CurlAsyncHTTPClient',
    'simple': 'tornado.simple_httpclient.SimpleAsyncHTTPClient'
}

# TODO: add logging
class HTTP(object):
    """HTTP Client with built-in AWS Signature version 4 support.
    
    HTTP requests are encoded with AWS signing signature required for secure API access.
    """
    def __init__(self, creds, endpoint, impl='curl', svc_cons_cls=ServiceConstants):
        """ Initialize instance with tornado client implemenation
        
        Parameters:
            creds: aws credentials
            endpoint: aws service enpoint
            impl: tornado client implemenation
            svc_cons_cls: ServiceConstants class
        """
        AsyncHTTPClient.configure(TORNADO_IMPL[impl])
        self.client = HTTPClient()
        self.cons = svc_cons_cls.from_url(endpoint)
        self.auth = auth.Authorization(self.cons, creds)

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
            qs: querystring
            
        Returns request signing headers
        """
        now = datetime.utcnow()
        amzdate = self._amzdate(now)
        dtstamp = self._datestamp(now)
        
        # Generate 'Authorization' header for signing request
        print 'AMZDATE=%s' % amzdate
        print 'DSTAMP=%s' % dtstamp
        print 'METHOD=%s' % method
        print 'PATH=%s' % path
        print 'QS=%s' % qs

        auth_header = self.auth.header(amzdate, dtstamp, path, method, qs, {'x-amz-date':amzdate}, payload)
        print 'AUTHORIZATION=%s' % auth_header

        # Set HTTP headers for request
        signed = {'x-amz-date':amzdate, 'Authorization': auth_header}
        return signed if not headers else dict(headers, **signed)

    def get(self, path, headers=None, qs=''):
        """ GET request

        Parameters:
            path: uri
            headers: HTTP headers

        Returns HTTP response object
        """
        url     = self.cons.url + path
        method  = 'GET'
        headers = self.sign(path, method, headers, qs)
        request = HTTPRequest(url, method, headers)

        return self.client.fetch(request)
    
    def post(self, path, payload, headers=None, qs=''):
        """ POST request
        
        Parameters:
            path: uri
            payload: request body
            headers: HTTP headers

        Returns HTTP response object
        """
        url     = self.cons.url + path
        method  = 'POST'
        headers = self.sign(path, method, headers, qs, payload)
        request = HTTPRequest(url, method, headers, body=payload)

        return self.client.fetch(request)
