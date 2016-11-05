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

# Used for testing header aggregation
class DynamoDBServiceConstants(Sigv4ServiceConstants):
    __REQUIRED_HEADERS = {'content-type':None, 'x-amz-target': None}

    def __init__(self, *args):
        super(DynamoDBServiceConstants, self).__init__(*args)
        self.__headers = self._merge(super(DynamoDBServiceConstants, self).headers,
                                     self.__REQUIRED_HEADERS)

    @property
    def headers(self):
        return self.__headers

class TestServiceConstants(object):
    
    def test_defaults(self):
        consts = default_service_constants()

        tools.assert_equal(consts.host, HOST)
        tools.assert_equal(consts.service, SERVICE)
        tools.assert_equal(consts.region, REGION)
        print 'HEADERS ', consts.headers
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

    def test_header_aggregation(self):
        consts = DynamoDBServiceConstants.from_url('https://dynamodb.us-west-2.amazonaws.com')
        
        print 'DYNAMODB HEADERS ', consts.headers
        tools.assert_equals(consts.headers, {'host': 'dynamodb.us-west-2.amazonaws.com',
                                             'x-amz-date': None,
                                             'content-type': None,
                                             'x-amz-target': None})
