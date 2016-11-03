import copy
import re

class ServiceConstants(object):
    """Logical grouping of AWS service constants

    Each AWS service has a list of values representative of its configuration;
    this class serves as a base set of these parameters.

    Sublclasses should override `URL_REGEX` for `from_url` inherited behavior to
    work properly.  See URL_REGEX comments below for more information.

    Example:
        class DynamoDBServiceConstants(ServiceConstants):
            URL_REGEX = re.compile(....)
            
            def __init__(self, *args, dynamo_foo=None, dynamo_bar=None):
                super(DynamoDBServiceConstants, self).__init__(*args):
                self.dynamo_foo = dynamo_foo
                self.dynamo_bar = dynamo_bar
    """
    # Minimum required headers for signing requests
    HEADERS = {'host': None, 'x-amz-date': None}

    # Parsed by 'from_url' method.  Matched group array is passed as *args list to
    # constructor so ordinal positions of match values must match constructor args
    # respectively.
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
        """Merges headers
        
        Parameters:
            override: dict overrides
            
        Returns merged header dict
        """
        merged = copy.copy(self.HEADERS)
        merged.update(override)
        return merged
 
    @property
    def url(self):
        return 'https://%s' % self.host

    @classmethod
    def from_url(cls, url, pattern=None, **kwargs):
        """Constructs ServiceConstants instance

        Parameters:
            url: url endpoint
            pattern: regex override pattern
            kwargs: passthru kwargs

        Returns class instance
        """
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
