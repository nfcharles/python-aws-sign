from aws_sign.v4 import Sigv4ServiceConstants
from aws_sign.client import http

import re

class APIGatewayServiceConstants(Sigv4ServiceConstants):
    URL_REGEX = re.compile(r"""(https)://      # scheme
                               (\w+            # api prefix
                               \.
                               ([\w\-]+)       # service
                               \.
                               ([\w\-]+)       # region
                               .amazonaws.com)
                               \/
                               ([\w]+)$        # stage""", re.X)
        
    def __init__(self, *args):
        super(APIGatewayServiceConstants, self).__init__(*args[:4])
        self.stage = args[4]

    def path(self, *args):
        return '%s/%s' % (self.stage, '/'.join(args))
        
    def __str__(self):
        return '%s\nstage=%s' % (super(APIGatewayServiceConstants, self).__str__(), self.stage)
    
    
def get_instance(endpoint, *args, **kwargs):
    return http.get_instance(endpoint, APIGatewayServiceConstants, *args, sign=True, **kwargs)
