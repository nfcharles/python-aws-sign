from aws_sign import ServiceConstants
from aws_sign.v4 import auth
from nose import tools

def get_constants():
    return ServiceConstants.from_url('foo-service.bar-region.amazonaws.com')

class Credentials(object):
    def __init__(self, access, secret):
        self.access_key = access
        self.secret_key = secret

def get_creds(access='foo', secret='bar'):
    return Credentials(access, secret)

def get_auth(consts, creds):
    return auth.Authorization(consts, creds)


class TestAuthorization(object):
    
    def test_string_to_sign(self):
        consts = get_constants()
        creds  = get_creds()
        awth   = get_auth(consts, creds)
        
        amzdate = '20160101T000000Z'
        cred_scope = 'foo-scope'
        canon_request = 'bar-request'
        str_to_sign = awth.string_to_sign(amzdate, cred_scope, canon_request)

        sign = ('AWS4-HMAC-SHA256', '20160101T000000Z', 'foo-scope', 
                '265bb9dcf4e69142011635054b77e00771b351626a2e81c680d09acc1a2e130d')
        
        expected = '\n'.join(sign)
        tools.assert_equal(str_to_sign, expected)

    def test_sign(self):
        consts = get_constants()
        creds  = get_creds()
        
        sign = auth.Authorization.sign('foo-key', 'bar-msg')
        tools.assert_equal(sign, "2\xce?\xb4\x12`\xd9\xb2\xae\xe2\xe9\x14\x0c\x837\xca\x13\r\x95\xd7\x93r}\xa1D\xf4\xa6\xb1\xc0Y\xd8\xc4")


    def test_signature_key(self):
        consts = get_constants()
        creds  = get_creds()
        awth   = get_auth(consts, creds)

        key = awth.signature_key('20160101')
        tools.assert_equal(key, "\xbbX\x80\x8f?\xa6\xc3\x10\xc2ZS\x10\xc5\xd9\xf0\xd7!\x88\xe9N\x9a.S9\xc3\xde\xd6'\xba-e\x08")

    def test_signature(self):
        consts = get_constants()
        creds  = get_creds()
        awth   = get_auth(consts, creds)

        signature = awth.signature('20160101', 'foo')
        tools.assert_equal(signature, 'c74cca597d58548aa5e340535f11dcfa93c3652ada09885426bfb08346b229df')

    def test_header(self):
        consts = get_constants()
        creds  = get_creds()
        awth   = get_auth(consts, creds)
        
        amzdate = '20160101T000000Z'
        hdrs    = {'x-amz-date': amzdate}
        stamp   = '20160101'
        uri     = '/'
        qs      = ''
        meth    = 'GET'
        load    = ''
        header  = awth.header(hdrs, amzdate, stamp, uri, qs, meth, load)

        expected = 'AWS4-HMAC-SHA256 ' + \
            'Credential=foo/20160101/bar-region/foo-service/aws4_request, ' + \
            'SignedHeaders=host;x-amz-date, ' + \
            'Signature=68c1d68a71091e8b93ce4d06b08c1cd35c9688b02d50be1f2ef394a45e1b6bfa'
        tools.assert_equal(header, expected)
