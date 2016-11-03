import os
import sys
import hmac
import copy
import json
import base64
import pprint
import hashlib
import tornado
import datetime
import requests

class ArgumentBuilder(object):
    def __init__(self, constants):
        self.constants = constants

    @staticmethod
    def payload_hash(payload=''):
        return hashlib.sha256(payload).hexdigest()

    def _build_query_string(self, **kwargs):
        keys = sorted(kwargs.keys())
        return '&'.join(['%s=%s' % (k, kwargs[k]) for k in keys])

    def _merge_headers(self, headers):
        tmp = copy.copy(self.constants.headers)
        tmp.update(headers)
        return tmp

    def signed_headers(self, headers):
        hdrs = self._merge_headers(headers)
        return ';'.join(sorted([k.lower() for k in hdrs.keys()]))

    def canonical_uri(self):
        return self.constants.url

    def canonical_query_string(self, **kwargs):
        return self._build_query_string(**kwargs)

    def canonical_headers(self, headers):
        """Returns canonical headers. """
        hdrs = self._merge_headers(headers)
        pairs = sorted([(k.lower(), k) for k in hdrs.keys()])
        return ''.join('%s:%s\n' % (k, hdrs[raw]) for k, raw in pairs)

    def canonical_request(self, method, uri, qs, headers, payload=''):
        return '\n'.join(['%s']*6) % \
            (method, 
             uri, 
             qs, 
             self.canonical_headers(headers), 
             self.signed_headers(headers),
             ArgumentBuilder.payload_hash(payload))

    def credential_scope(self, datestamp):
        return '%s/%s/%s/%s' % \
            (datestamp, 
             self.constants.region, 
             self.constants.service,
             self.constants.signing)
