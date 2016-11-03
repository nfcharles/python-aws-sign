import copy
import re

class ServiceConstants(object):
    # Minimum required headers for signing requests
    HEADERS = {'host': None, 'x-amz-date': None}

    URL_REGEX = re.compile(r"""(?:https://)?    # scheme
                               (([\w\-]+)       # service
                               \.
                               ([\w\-]+)        # region
                               .amazonaws.com$) # rest """, re.X)

    def __init__(self, host, service, region, algorithm='AWS4-HMAC-SHA256', signing='aws4_request', headers=None):
        self.host      = host
        self.service   = service
        self.region    = region
        self.algorithm = algorithm
        self.signing   = signing
        self.headers   = headers if headers else self._merge({'host': host})
    
    def _merge(self, override):
        merged = copy.copy(self.HEADERS)
        merged.update(override)
        return merged
 
    @property
    def url(self):
        return 'https://%s' % self.host

    @classmethod
    def from_url(cls, url, pattern=None, **kwargs):
        regex = cls.URL_REGEX
        if pattern:
            regex = re.compile(pattern)
        ret = regex.match(url)
        if ret:
            return cls(*ret.groups(), **kwargs)
        else:
            raise Exception('Error parsing url: %s' % url)

    def __str__(self):
        return 'host=%s\nservice=%s\nregion=%s\nalgorithm=%s\nsigning=%s\nheaders=%s' % \
            (self.host, self.service, self.region, self.algorithm, self.signing, self.headers)
