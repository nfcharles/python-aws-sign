from .. import ServiceConstants

from nose import tools

SERVICE   = 'foo-service'
REGION    = 'bar-region'
HOST      = '%s.%s.amazonaws.com' % (SERVICE, REGION)
ALGORITHM = 'AWS4-HMAC-SHA256'
SIGNING   = 'aws4_request'

def default_service_constants():
    return ServiceConstants(
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
        consts = ServiceConstants.from_url(HOST)
        
        tools.assert_equals(consts.host, HOST)
        tools.assert_equals(consts.service, SERVICE)
        tools.assert_equals(consts.region, REGION)
        tools.assert_equal(consts.algorithm, ALGORITHM)
        tools.assert_equal(consts.signing, SIGNING)
        
    def test_from_url_with_scheme(self):
        consts = ServiceConstants.from_url('https://%s' % HOST)
        
        tools.assert_equals(consts.host, HOST)
        tools.assert_equals(consts.service, SERVICE)
        tools.assert_equals(consts.region, REGION)        

    def test_from_url_kwargs_override(self):
        headers   = {'foo-header': 'foo'}
        algorithm = 'foo'
        signing   = 'bar'
        consts = ServiceConstants.from_url(HOST, 
                                           headers=headers,
                                           algorithm=algorithm,
                                           signing=signing)
        
        tools.assert_equals(consts.host, HOST)
        tools.assert_equals(consts.service, SERVICE)
        tools.assert_equals(consts.region, REGION)
        tools.assert_equals(consts.headers, headers)
        tools.assert_equals(consts.algorithm, algorithm)
        tools.assert_equals(consts.signing, signing)
        

    @tools.raises(Exception)
    def test_bad_url_scheme(self):
        # Should be https
        ServiceConstants.from_url('http://foo.bar.amazonaws.com')

    @tools.raises(Exception)
    def test_bad_host_suffix(self):
        # Should include 'amazonaws.com' suffix
        ServiceConstants.from_url('https://foo.bar')


    def test_url_pattern_override(self):
        service = 'foo'
        region  = 'bar'
        host = '%s.%s' % (service, region)
        url  = 'https://%s' % host
        consts = ServiceConstants.from_url(url, 
                                           pattern='https://((\w+)\.(\w+))')

        print consts        
        tools.assert_equal(consts.host, host)
        tools.assert_equal(consts.service, service)
        tools.assert_equal(consts.region, region)


    def test_url(self):
        host = 'foo.bar.amazonaws.com'
        consts = ServiceConstants(
            host=host,
            service='foo',
            region='bar')

        tools.assert_equals(consts.url, 'https://%s' % host)
