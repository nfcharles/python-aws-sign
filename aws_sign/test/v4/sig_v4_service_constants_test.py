from aws_sign.v4 import Sigv4ServiceConstants

from nose import tools

SERVICE   = 'foo-service'
REGION    = 'bar-region'
HOST      = '%s.%s.amazonaws.com' % (SERVICE, REGION)
ALGORITHM = 'AWS4-HMAC-SHA256'
SIGNING   = 'aws4_request'

def default_service_constants():
    return Sigv4ServiceConstants(
        HOST,
        SERVICE,
        REGION)

class TestServiceConstants(object):
    
    def test_defaults(self):
        consts = default_service_constants()

        tools.assert_equal(consts.host, HOST)
        tools.assert_equal(consts.service, SERVICE)
        tools.assert_equal(consts.region, REGION)
        tools.assert_equal(consts.headers, {'host': HOST, 'x-amz-date': None})
        tools.assert_equal(consts.algorithm, ALGORITHM)
        tools.assert_equal(consts.signing, SIGNING)

    def test_from_url(self):
        consts = Sigv4ServiceConstants.from_url(HOST)
        
        tools.assert_equals(consts.host, HOST)
        tools.assert_equals(consts.service, SERVICE)
        tools.assert_equals(consts.region, REGION)
        tools.assert_equal(consts.algorithm, ALGORITHM)
        tools.assert_equal(consts.signing, SIGNING)
        
    def test_from_url_with_scheme(self):
        consts = Sigv4ServiceConstants.from_url('https://%s' % HOST)
        
        tools.assert_equals(consts.host, HOST)
        tools.assert_equals(consts.service, SERVICE)
        tools.assert_equals(consts.region, REGION)        
        tools.assert_equal(consts.algorithm, ALGORITHM)
        tools.assert_equal(consts.signing, SIGNING)
