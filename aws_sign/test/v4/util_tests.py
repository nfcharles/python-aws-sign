from nose import tools

from aws_sign.v4.util import safe_encode


class TestSafeEncode(object):

    def test_unicode(self):
        before = u'howdy'
        after = safe_encode(before)
        expected = b'howdy'
        tools.assert_equal(after, expected)
        tools.assert_equal(type(after), type(expected))

    def test_bytes(self):
        before = b'howdy'
        after = safe_encode(before)
        expected = b'howdy'
        tools.assert_equal(after, expected)
        tools.assert_equal(type(after), type(expected))

    def test_natural(self):
        before = 'howdy'
        after = safe_encode(before)
        expected = b'howdy'
        tools.assert_equal(after, expected)
        tools.assert_equal(type(after), type(expected))
