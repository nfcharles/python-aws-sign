from aws_sign.v4.canonical import ArgumentBuilder
from aws_sign.v4 import Sigv4ServiceConstants
from nose import tools

def get_constants():
    return Sigv4ServiceConstants.from_url('https://foo-service.bar-region.amazonaws.com')

def get_builder(c):
    return ArgumentBuilder(c)

class TestCanonical(object):

    def test_canonical_headers(self):
        """Tests canonical header format.

        Headers should be
          1. lower case
          2. sorted in ascending lexograhpical order
          """

        c = get_constants()
        canon = get_builder(c)
        amzdate = '20160101T000000Z'

        # Test default
        headers = canon.canonical_headers(amzdate=amzdate)

        
        tools.assert_equal(headers, 'host:%s\nx-amz-date:%s\n' % (c.host, amzdate))
        
        # Test additional
        headers = canon.canonical_headers(
            amzdate=amzdate, 
            headers={
                'x-amz-B': 'B',
                'x-amz-a': 'A'
                })
        
        tools.assert_equal(headers, 'host:%s\nx-amz-a:A\nx-amz-b:B\nx-amz-date:%s\n' % \
                               (c.host, amzdate))

    def test_signed_headers(self):
        c = get_constants()
        canon = get_builder(c)

        signed_headers = canon.signed_headers()
        tools.assert_equal(signed_headers, 'host;x-amz-date')

        signed_headers = canon.signed_headers(['x-amz-B', 'x-amz-a'])
        tools.assert_equal(signed_headers, 'host;x-amz-a;x-amz-b;x-amz-date')
        
    def test_canonical_request(self):
        c = get_constants()
        canon = get_builder(c)
        
        method = 'GET'
        uri = '/'
        qs = ''
        amzdate = '20160101T000000Z'

        # Request - 1
        canon_request = canon.canonical_request(amzdate, uri, method, qs)
        request = ('GET', '/', '', 
                   'host:foo-service.bar-region.amazonaws.com',
                   'x-amz-date:20160101T000000Z', '', 'host;x-amz-date', 
                   'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')
        expected = '\n'.join(request)
        tools.assert_equal(canon_request, expected)


        # Request - 2
        headers = {'x-amz-Foo': 'foo', 'x-amz-bar': 'bar'}
        canon_request = canon.canonical_request(amzdate, uri, method, qs, headers)
        request = ('GET', '/', '', 
                   'host:foo-service.bar-region.amazonaws.com',
                   'x-amz-bar:bar', 'x-amz-date:20160101T000000Z', 'x-amz-foo:foo',
                   '', 'host;x-amz-bar;x-amz-date;x-amz-foo', 
                   'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')

        expected = '\n'.join(request)
        tools.assert_equal(canon_request, expected)


    def test_credential_scope(self):
        c = get_constants()
        canon = get_builder(c)

        datestamp = '20160101'
        scope = canon.credential_scope(datestamp)
        tools.assert_equal(scope, '20160101/bar-region/foo-service/aws4_request')

    def test_query_string(self):
        tools.assert_equal(ArgumentBuilder.canonical_query_string(), '')

        qs = ArgumentBuilder.canonical_query_string({'foo': 1, 'bar': 2, 'baz': 3})
        tools.assert_equal(qs, 'bar=2&baz=3&foo=1')

        qs = ArgumentBuilder.canonical_query_string({'foo bar': 1, 'baz': 2})
        tools.assert_equal(qs, 'baz=2&foo+bar=1')
