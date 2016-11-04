from .. import ServiceConstants

class Sigv4ServiceConstants(ServiceConstants):
    """Logical grouping of Signature Version 4 service constants

    This class sets the appropriate Signature v4 specific parameters required
    for signing.
    """
    # Minimum required headers for signature v4 signed requests
    HEADERS = {'host': None, 'x-amz-date': None}

    def __init__(self, host, service, region, headers=None):
        """Initializes v4 specific constants

        Parameters
            host: service host
            service: service name
            region: service region
            """
        super(Sigv4ServiceConstants, self).__init__(host,
                                                    service,
                                                    region,
                                                    algorithm='AWS4-HMAC-SHA256',
                                                    signing='aws4_request')
        self.headers = headers if headers else self._merge({'host':host})
    
    
