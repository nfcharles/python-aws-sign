"""Utility functions for aws-sign"""

def safe_encode(s):
    """
    Attempt to encode a string with UTF-8, regarding some exceptions as indicating that it is already in that state.

    The `hashlib` functions tend to require parameters to be byte strings, rather than Unicode, but it is tricky
    to handle all the possibilities in both Python 2 and 3 environments.  This tries to encode a string as UTF-8.
    It catches tell-tale exceptions indicating that the passed in string is already a byte string.

    :param s: any sort of string
    :return: a byte string ('str' in Python 2, 'bytes' in Python 3)
    """
    try:
        return s.encode('utf-8')
    except (AttributeError, UnicodeDecodeError):
        return s
