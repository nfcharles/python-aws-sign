import hmac
import hashlib

from . import canonical


class Authorization(object):
    def __init__(self, constants,  creds):
        self.constants = constants
        self.canonical_builder = canonical.ArgumentBuilder(constants)
        self.creds = creds

    @staticmethod
    def sign(key, msg):
        return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

    def _header(self, credential_scope, signed_headers, signature):
        return '%s Credential=%s/%s, SignedHeaders=%s, Signature=%s' \
            % (self.constants.algorithm, self.creds.access_key, credential_scope, signed_headers, signature)

    def string_to_sign(self, amzdate, credential_scope, canonical_request):
        return '%s\n%s\n%s\n%s' % \
            (self.constants.algorithm, 
             amzdate, 
             credential_scope, 
             hashlib.sha256(canonical_request).hexdigest())

    def signature(self, datestamp, string_to_sign):
        return hmac.new(self.signature_key(datestamp), (string_to_sign).encode('utf-8'), hashlib.sha256).hexdigest()

    def signature_key(self, date_stamp):
        date    = Authorization.sign(('AWS4' + self.creds.secret_key).encode('utf-8'), date_stamp)
        region  = Authorization.sign(date, self.constants.region)
        service = Authorization.sign(region, self.constants.service)
        signing = Authorization.sign(service, self.constants.signing)
        return signing

    def header(self, amzdate, datestamp, uri, method='GET', qs='', headers=None, payload=''):
        headers = headers if headers else {}
        credential_scope  = self.canonical_builder.credential_scope(datestamp)
        canonical_request = self.canonical_builder.canonical_request(amzdate, uri, method, qs, headers, payload)
        signed_headers    = self.canonical_builder.signed_headers(headers.keys())
        string_to_sign    = self.string_to_sign(amzdate, credential_scope, canonical_request)
        signature         = self.signature(datestamp, string_to_sign)

        return self._header(credential_scope, signed_headers, signature)
