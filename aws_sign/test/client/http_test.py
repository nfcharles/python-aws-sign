from aws_sign import URLParseException
from aws_sign.client import http
from copy import deepcopy
from nose import tools

_merge = http._merge
_normalize = http._normalize


class TestHTTP(object):
    
    def test_normalize(self):
        a = {'Foo': 1, 'BAR': {'Foo-Bar': {'foo-baz': 4}}}
        expected = {'foo': 1, 'bar': {'foo-bar': { 'foo-baz': 4}}} 
        tools.assert_equal(_normalize(a), expected)


    def test_merge(self):
        a = {'foo': 1, 'bar': {'foobar': 'baz' }}
        b = {'foo': 1, 'bar': {'foobar': 'foo' }, 'baz': 'foo'}
        
        expected = {'foo': 1, 'bar': {'foobar':'foo'}, 'baz':'foo'} 
        tools.assert_equal(_merge(deepcopy(a), b), expected)

        expected = {'foo': 1, 'bar': {'foobar':'baz'}, 'baz':'foo'}
        tools.assert_equal(_merge(deepcopy(b), a), expected)

        c = {'foo': 'bar'}
        d = {'foo': 'bar'}
        tools.assert_equal(_merge(deepcopy(c), d), c)
        
        e = {1: {2: {3: {4: {'foo': 'bar'}}}}, 5: 'baz'}
        f = {0: 'foo', 1: {2: {3: {4: {'foo': 'foobar'}}}}}
        
        expected = {0: 'foo', 1: {2: {3: {4: {'foo': 'foobar'}}}}, 5: 'baz'}
        tools.assert_equal(_merge(deepcopy(e), f), expected)

        expected = {0: 'foo', 1: {2: {3: {4: {'foo': 'bar'}}}}, 5: 'baz'}
        tools.assert_equal(_merge(deepcopy(f), e), expected)
        
             
    @tools.raises(http.UnknownCredentialsException)
    def test_raise_unknown_creds(self):
        http.get_instance('https://mock-service.us-west-2.amazonaws.com', sign=True)


    def test_normalized_merged(self):
        # Test for merging headers -- headers are case insensitive and can be 
        # set in multiple places.  This allows for possible mismatched headers.
        # Normalizing before merges assures that like headers get overridden
        # appropriately
        a = {'Foo': 'bar'}
        b = {'foo': 'bar'}
        ret  = _merge(_normalize(deepcopy(a)), _normalize(b))
        tools.assert_equal(ret, b)

        c = {'Foo': {'baR': 1, 'baz': { 'foo-bar': 2 }}}
        d = {'foO': {'Bar': 1, 'baz': { 'Foo-baR': 22222 }}}
        ret  = _merge(_normalize(deepcopy(c)), _normalize(d))
        tools.assert_equal(ret, {'foo': {'bar': 1, 'baz': { 'foo-bar': 22222 }}})
        

    def test_default_service_constants(self):
        endpoint = 'http://localhost:8888'
        const = http.DefaultServiceConstants.from_url(endpoint)
        tools.assert_equal(const.scheme, 'http')
        tools.assert_equal(const.host, 'localhost')
        tools.assert_equal(const.port, 8888)
        tools.assert_equal(const.url, endpoint)

        endpoint = 'https://localhost'
        const = http.DefaultServiceConstants.from_url(endpoint)
        tools.assert_equal(const.scheme, 'https')
        tools.assert_equal(const.host, 'localhost')
        tools.assert_equal(const.port, None)
        tools.assert_equal(const.url, endpoint)


    @tools.raises(URLParseException)
    def test_bad_port(self):
        foo = http.DefaultServiceConstants.from_url('http://localhost:888P')
        
