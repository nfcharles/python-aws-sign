import copy
import hashlib
from six.moves.urllib import parse

from .util import safe_encode

class ArgumentBuilder(object):
    """Constructs requiste arguments for Signature version 4 signing.

    ServiceConstants are used in part to build the various arguments.
    """
    def __init__(self, constants):
        self.constants = constants

    @staticmethod
    def payload_hash(payload):
        """Hashes input string
        
        Parameter:
            payload: String to hash

        Returns hashed string
        """
        return hashlib.sha256(payload).hexdigest()

    @staticmethod
    def canonical_query_string(query_args=None):
        """Preprocess query string for signing
        
        foo = CLS.canonical_query_string({'amz-Foo': 'FOO', 'amz-bar': 'BAR'})
          where foo = 'amz-bar=BAR&amz-Foo=FOO'
          
        Parameters:
            query_args: query parameters dict
    
        Returns sorted, urlencoded querystring in string format
        """
        if query_args is None:
            return ''
        else:
            items = sorted(query_args.items(), key=lambda i: i[0])
            return parse.urlencode(items, True)

    def _merge_headers(self, headers):
        """Merges input headers with default headers 

        Parameters:
           headers: dict of (header, value)

        Returns dict of merged headers
        """
        tmp = copy.copy(self.constants.headers)
        tmp.update(headers)
        return tmp
        
    def signed_headers(self, headers=None):
        """ Returns ; delimited list of all headers comprising signature 

        Parameters:
            headers: list of extra headers -- apart from default defined in
            constants

        Returns sorted list of header names that is merge of input list and 
        default headers"""
        if not headers:
            headers = []
        return ';'.join(sorted([name.lower() for name in 
                                set(list(self.constants.headers.keys()) + headers)]))

    def canonical_headers(self, amzdate, headers=None):
        """Constructs canonical headers
        
        Parameters:
            amzdate: '%Y%m%dT%H%M%sZ' timestamp 
            headers: optional dict of additional headers
            
        Return sorted list of canonical headers for signing proces
        """
        amzd = {'x-amz-date': amzdate}
        hdrs = self._merge_headers(dict(headers, **amzd) if headers else amzd)
        pairs = sorted([(k.lower(), k) for k in hdrs.keys()])
        return ''.join('%s:%s\n' % (k, hdrs[raw]) for k, raw in pairs)

    def canonical_request(self, amzdate, uri, method, qs, headers=None, payload=''):
        """Constructs canonical request
        
        Parameters:
            amzdate: '%Y%m%dT%H%M%sZ' timestamp
            uri:     HTTP uri, e.g. /foo/bar
            method:  HTTP method, e.g. 'GET', 'POST', etc
            qs:      url querystring
            headers: optional list of additional headers used for signing
            payload: optional payload -- relevant in 'POST' requests
            
        Returns canonical request string
        """
        return '\n'.join(['%s']*6) % \
            (method, 
             uri, 
             qs, 
             self.canonical_headers(amzdate, headers), 
             self.signed_headers(list(headers.keys()) if headers else None),
             ArgumentBuilder.payload_hash(safe_encode(payload)))

    def credential_scope(self, datestamp):
        """Constructs signing credential scope 
        
        Parameters:
            datestamp: '%Y%m%d' date

        Returns credential scope string
        """
        return '%s/%s/%s/%s' % \
            (datestamp, 
             self.constants.region, 
             self.constants.service,
             self.constants.signing)
