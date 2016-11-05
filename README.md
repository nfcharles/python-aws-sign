# AWS Sign #

AWS Sign provides classes for signing AWS HTTP requests adhering to the signature version 4 specification.  

Additionally, a tornado based client capable of sending signature v4 signed requests is provided.


## Classes ##

### ServiceConstants ###

Request signing requires many inputs, one of which is a set of values representing the
AWS service : this includes, but not limited:
* host
* service name
* region
* signing algorithm

`ServiceConstants` provides a logical grouping of these values.

Services that require more constants can subclass `ServiceConstants` and inherent default behaviors.  As an example, consider a class representing APIGateway.  `ServiceConstants` doesn't sufficiently represent all the constants needed to sign requests so we must create a sublcass.

```python
class APIGatewayServiceConstants(Sigv4ServiceConstants):
    # Parsed by 'from_url' method.  Matched group array is passed as *args list to
    # constructor so ordinal positions of match values must match constructor args.
    URL_REGEX = re.compile(r"""(?:https://)?   # scheme
                               (\w+            # api prefix
                               \.
                               ([\w\-]+)       # service
                               \.
                               ([\w\-]+)       # region
                               .amazonaws.com)
                               \/
                               ([\w]+)$        # stage""", re.X)
    
    def __init__(self, *args):
        """
        Parameters
            host: service host
            service: service name
            region: service region
            stage: api gateway stage
        """
        super(APIGatewayServiceConstants, self).__init__(*args[:3])
        self.stage = args[3]
    
    @property
    def url(self):
        return 'https://%s/%s' % (self.host, self.stage)

    def __str__(self):
        return 'host=%s\nservice=%s\nregion=%s\nstage=%s\nalgorithm=%s\nsigning=%s\nheaders=%s' % \
            (self.host, self.service, self.region, self.stage, self.algorithm, self.signing, self.headers)
```

Consider another example using dynamodb

```python
class DynamoDBServiceConstants(Sigv4ServiceConstants):
    __REQUIRED_HEADERS = {'content-type':None, 'x-amz-target': None}

    def __init__(self, *args):
        super(DynamoDBServiceConstants, self).__init__(*args)
        self.__headers = self._merge(super(DynamoDBServiceConstants, self).headers,
                                     self.__REQUIRED_HEADERS)

    @property
    def headers(self):
        return self.__headers
```


### Authorization ###

`auth.Authorization` encapsulates the signing behavior.  Essentially, it generates a hash value for given
inputs that is used as an HTTP header value (Authoriaztion) -- or alternatively a querystring parameter.

```python
...

a = auth.Authorization(ServiceConstants(*args), Credentials())

# Sign request
http_headers['Authoriaztion'] = a.header(**kwargs)

...
```


## Client ##

TBD

# License #

AWS Sign is free software and is released under the terms
of the MIT license (<http://opensource.org/licenses/mit-license.php>),
as specified in the accompanying LICENSE.txt file.
