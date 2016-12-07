from . import http
from aws_sign.v4 import Sigv4ServiceConstants

import re

class APIGatewayServiceConstants(Sigv4ServiceConstants):
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
        super(APIGatewayServiceConstants, self).__init__(*args[:3])
        self.stage = args[3]
        
    def __str__(self):
        return 'host=%s\nservice=%s\nregion=%s\nstage=%s\nalgorithm=%s\nsigning=%s\nheaders=%s' % \
            (self.host, self.service, self.region, self.stage, self.algorithm, self.signing, self.headers)

    
def get_instance(endpoint, *args, **kwargs):
    return http.get_instance(endpoint, APIGatewayServiceConstants, *args, **kwargs)

