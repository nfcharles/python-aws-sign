import copy
import re

class URLParseException(Exception):
    def __init__(self, url, url_format):
        super(URLParseException, self).__init__('Unable to parse url %s.  Expected format=%s' % (url, url_format))

class ServiceConstants(object):
    """Logical grouping of AWS service constants

    Each AWS service has a list of values representative of its configuration;
    this class serves as a base set of these parameters.

    Subclasses should override `URL_REGEX` if url pattern deviates from standard form (this
    is the case when there's additional information to parse in the url); required for `from_url` 
    inherited behavior to work properly.  See URL_REGEX comments below for more information.

    __REQUIRED_HEADERS and __header conventions should be used for aggregating required
    headers among all subclasses.  See example.

    Example:
        class FooServiceConstants(ServiceConstants):
            __REQUIRED_HEADERS = {'foo-header':None, 'bar-header':None}
            URL_REGEX = re.compile(...)

            def __init__(self, *args):
                super(FooServiceConstants, self).__init__(*args[:-1]):
                self.foo = args[-1]
                self.__headers = self._merge(super(FooServiceConstants, self).headers,
                                             self.__REQUIRED_HEADERS)

            @property
            def headers(self):
                return self.__headers

    Let's assume ServiceConstants has 'baz-header' as required header, then
    
    Example:
      fsc = FooServiceConstants(*args):
      headers = fcs.headers
      
      # headers -> {'baz-header': None,
      #             'foo-header': None,
      #             'bar-header': None }
      #
      # where 'baz-header' is derived from the base class ServiceConstants
    """
    # Minimum required headers for signing requests
    __REQUIRED_HEADERS = {}

    FORMAT = 'http[s]?://[\w\-\.]+amazonaws.com'

    # Parsed by 'from_url' method.  Matched group array is passed as *args list to
    # constructor so ordinal positions of match values must match constructor args
    # respectively.
    URL_REGEX = re.compile(r"""^(http[s]?)://    # scheme
                                (([\w\-]+)       # service
                                \.
                                ([\w\-]+)        # region
                                .amazonaws.com$) # rest """, re.X)

    def __init__(self, scheme, host, service, region, algorithm, signing):
        self.scheme    = scheme
        self.host      = host
        self.service   = service
        self.region    = region
        self.algorithm = algorithm
        self.signing   = signing
        self.__headers = self.__REQUIRED_HEADERS
    
    def _merge(self, base, *args):
        """Merges headers
        
        Parameters:
            args: list of dicts to merge
            
        Returns merged header dict
        """
        source = copy.copy(base)
        for other in args:
            source.update(other)
        return source
 
    @property
    def url(self):
        return '%s://%s' % (self.scheme, self.host)

    @property
    def headers(self):
        return self.__headers

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
            raise URLParseException(url, cls.FORMAT)

    def path(self, *args):
        return '/'.join(args)

    def __str__(self):
        return 'scheme=%s\nhost=%s\nservice=%s\nregion=%s\nalgorithm=%s\nsigning=%s\nheaders=%s' % \
            (self.scheme, self.host, self.service, self.region, self.algorithm, self.signing, self.headers)
