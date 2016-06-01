import json
import os

import requests

from regparser.tree.struct import node_decode_hook
import settings


class Client:
    """A very simple client for accessing the regulation and meta data."""

    def __init__(self):
        self.base_url = settings.API_BASE

    def layer(self, layer_name, label, version):
        """End point for layer JSON. Return the result as a list"""
        return self._get("layer/%s/%s/%s" % (layer_name, label, version))

    def notices(self):
        """End point for notice searching. Right now, just a list"""
        return self._get("notice")

    def notice(self, document_number):
        """End point for retrieving a single notice."""
        return self._get("notice/%s" % document_number)

    def _get(self, suffix):
        """Actually make the GET request. Assume the result is JSON. Right
        now, there is no error handling"""
        if self.base_url.startswith('http'):    # API
            json_str = requests.get(self.base_url + suffix).text
        else:   # file system
            if os.path.isdir(self.base_url + suffix):
                suffix = suffix + "/index.html"
            with open(self.base_url + suffix) as f:
                json_str = f.read()
        return json.loads(json_str, object_hook=node_decode_hook)
