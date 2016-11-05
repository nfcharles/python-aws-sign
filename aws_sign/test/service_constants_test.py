from .. import ServiceConstants

from nose import tools

SERVICE   = 'foo-service'
REGION    = 'bar-region'
HOST      = '%s.%s.amazonaws.com' % (SERVICE, REGION)
ALGORITHM = 'foo-algorithm'
SIGNING   = 'bar_request'
HEADERS   = {'foo-header-a': 'FOO!', 'foo-header-b': 'BAR!'}
ALG_SIGN  = {'algorithm':ALGORITHM, 'signing':SIGNING}

def default_service_constants():
    return ServiceConstants(
        HOST,
        SERVICE,
        REGION,
        ALGORITHM,
        SIGNING)

class TestServiceConstants(object):
    
    def test_defaults(self):
        consts = default_service_constants()
        print consts

        tools.assert_equal(consts.host, HOST)
        tools.assert_equal(consts.service, SERVICE)
        tools.assert_equal(consts.region, REGION)
        tools.assert_equal(consts.algorithm, ALGORITHM)
        tools.assert_equal(consts.signing, SIGNING)
        tools.assert_equal(consts.headers, {})

    def test_from_url(self):
        consts = ServiceConstants.from_url(HOST, **ALG_SIGN)
        
        tools.assert_equals(consts.host, HOST)
        tools.assert_equals(consts.service, SERVICE)
        tools.assert_equals(consts.region, REGION)
        tools.assert_equal(consts.algorithm, ALGORITHM)
        tools.assert_equal(consts.signing, SIGNING)
        
    def test_from_url_with_scheme(self):
        consts = ServiceConstants.from_url('https://%s' % HOST, **ALG_SIGN)
        
        tools.assert_equals(consts.host, HOST)
        tools.assert_equals(consts.service, SERVICE)
        tools.assert_equals(consts.region, REGION)        

    def test_from_url_kwargs_override(self):
        headers   = {'foo-header': 'foo'}
        consts = ServiceConstants.from_url(HOST, 
                                           #headers=headers,
                                           **ALG_SIGN)
        
        tools.assert_equals(consts.host, HOST)
        tools.assert_equals(consts.service, SERVICE)
        tools.assert_equals(consts.region, REGION)
        tools.assert_equals(consts.algorithm, ALGORITHM)
        tools.assert_equals(consts.signing, SIGNING)
        #tools.assert_equals(consts.headers, headers)
        

    @tools.raises(Exception)
    def test_bad_url_scheme(self):
        # Should be https
        ServiceConstants.from_url('http://foo.bar.amazonaws.com', **ALG_SIGN)

    @tools.raises(Exception)
    def test_bad_host_suffix(self):
        # Should include 'amazonaws.com' suffix
        ServiceConstants.from_url('https://foo.bar', **ALG_SIGN)


    def test_url_pattern_override(self):
        service = 'foo'
        region  = 'bar'
        host = '%s.%s' % (service, region)
        url  = 'https://%s' % host
        consts = ServiceConstants.from_url(url, 
                                           pattern='https://((\w+)\.(\w+))',
                                           **ALG_SIGN)

        print consts        
        tools.assert_equal(consts.host, host)
        tools.assert_equal(consts.service, service)
        tools.assert_equal(consts.region, region)


    def test_url(self):
        host = 'foo.bar.amazonaws.com'
        consts = ServiceConstants(
            host=host,
            service='foo',
            region='bar',
            **ALG_SIGN)

        tools.assert_equals(consts.url, 'https://%s' % host)
