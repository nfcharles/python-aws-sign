import hmac
import hashlib

from . import canonical


class Authorization(object):
    """Class for signing AWS HTTP requests adhering to Signature Version 4 specification
    
    Notable features include
      * request signing 
      * HTTP Authorization header generation

    Note that AWS HTTP requests can be encoded with signature data via
      * querystring parameter
      * HTTP request header
    """
    def __init__(self, constants, creds):
        """Initializes auth
        
        Parameters:
           constants: ServiceConstants
           creds:     AWS Credentials
        """
        self.constants = constants
        self.canonical_builder = canonical.ArgumentBuilder(constants)
        self.creds = creds

    @staticmethod
    def sign(key, msg):
        """Create message authentication signature
        
        Parameters:
            key: hash key
            msg: hash message
            
        Returns message authentication signature"""
        return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

    def _header(self, credential_scope, signed_headers, signature):
        """Creates HTTP header
        
        Parameters:
            credential_scope: Signature v4 credential scope string
            signed_headers: signed headers string
            signature: request hash signature
            
        Returns header string
        """
        return '%s Credential=%s/%s, SignedHeaders=%s, Signature=%s' \
            % (self.constants.algorithm, self.creds.access_key, credential_scope, signed_headers, signature)

    def string_to_sign(self, amzdate, credential_scope, canonical_request):
        """Creates string to string

        Parameters:
            amzdate: '%Y%m%dT%H%M%SZ' timestamp
            credential_scope: Signature v4 credential scope string
            canonical_request: Signature v4 canonical request string

        Return string to sign"""
        return '%s\n%s\n%s\n%s' % \
            (self.constants.algorithm, 
             amzdate, 
             credential_scope, 
             hashlib.sha256(canonical_request).hexdigest())

    def signature(self, datestamp, string_to_sign):
        """Creates signture of HTTP request
        
        Parameters:
            datestamp: '%Y%m%d' stamp
            string_to_string: hash input string
            
        Returns string signature"""
        return hmac.new(self.signature_key(datestamp), (string_to_sign).encode('utf-8'), hashlib.sha256).hexdigest()

    def signature_key(self, date_stamp):
        """Creates signing key
        
        Parameters:
            date_stamp: '%Y%m%d' stamp

        Returns signing key string"""
        date    = Authorization.sign(('AWS4' + self.creds.secret_key).encode('utf-8'), date_stamp)
        region  = Authorization.sign(date, self.constants.region)
        service = Authorization.sign(region, self.constants.service)
        signing = Authorization.sign(service, self.constants.signing)
        return signing

    def header(self, amzdate, datestamp, uri, method='GET', qs='', headers=None, payload=''):
        """Creates HTTP Authorization header
        
        Parameters:
            amzdate: '%Y%m%dT%H%M%SZ' timestamp
            datestamp: '%Y%m%d' date
            uri: /foo/bar
            method: HTTP method, e.g. 'GET', 'POST, etc
            qs: url querystring
            headers: additional HTTP request headers
            payload: 'POST' payload

        Returns HTTP header
        """
        headers = headers if headers else {}
        credential_scope  = self.canonical_builder.credential_scope(datestamp)
        canonical_request = self.canonical_builder.canonical_request(amzdate, uri, method, qs, headers, payload)
        signed_headers    = self.canonical_builder.signed_headers(headers.keys())
        string_to_sign    = self.string_to_sign(amzdate, credential_scope, canonical_request)
        signature         = self.signature(datestamp, string_to_sign)

        return self._header(credential_scope, signed_headers, signature)

    def headers(self, *args, **kwargs):
        """Returns all headers for signing

        Assumed AWS roles must also set the 'X-Amz-Security-Token' header in addition to 
        the 'Authorization' header.

        Returns headers dict
        """
        ret = {}
        if self.creds.token:
            ret['X-Amz-Security-Token'] = self.creds.token
        ret['Authorization'] = self.header(*args, **kwargs)
        return ret
