from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r"""
  name: netbird
  author:
  - Mark Horninger (@dominion.soltuions@mstdn.business) <mark.horninger@dominion.solutions>
  version_added: "0.0.2"
  requirements:
    - requests>=2.31.0
  short_description:
  description:
    -
  extends_documentation_fragment:
    - constructed
    - inventory_cache
  options:
    api_key:
      description: The API Key for the Netbird API.
      required: true
      type: string
      env:
        - name: NETBIRD_API_KEY
  notes:
    - if read in variable context, the file can be interpreted as YAML if the content is valid to the parser.
    - this lookup does not understand globbing --- use the fileglob lookup instead.
"""

EXAMPLES = r"""
"""
from ansible.errors import AnsibleError, AnsibleParserError
from ansible.utils.display import Display
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable

# Specific for the NetbirdAPI Class
import requests
import json

display = Display()

class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):
    NAME="dominion_solutions.netbird"

    def _build_client(self):
        """Build the Netbird API Client"""
        access_token = self.get_option('api_key')
        api_url = self.get_option('api_url')
        if access_token is None:
            raise AnsibleError("Could not retrieve the Netbird API Key from the configuration sources.")
        self.client = NetbirdApi(self.get_option('api_key'), self.get_option('api_url'))

    def _get_peer_inventory(self):
        """Get the inventory from the Netbird API"""
        return json.loads(self.client.ListPeers())

    def parse(self, inventory, loader, path, cache=True):
        """Dynamically parse the inventory from the Netbird API"""
        super(InventoryModule, self).parse(inventory, loader, path)
        self.peers = None

        self._read_config_data(path)
        cache_key = self.get_cache_key(path)

        if cache:
            cache = self.get_option('cache')
        update_cache = False
        if cache:
            try:
                self.peers = [Peer(None, i["id"], i) for i in self._cache[cache_key]]
            except KeyError:
                update_cache = True

        # Check for None rather than False in order to allow
        # for empty sets of cached instances
        if self.instances is None:
            self._build_client(loader)
            self._get_peer_inventory()

        if update_cache:
            self._cache[cache_key] = self._cacheable_inventory()

        self.populate()


### This is a very limited wrapper for the netbird API.
class NetbirdApi:
    def __init__ (self, api_key, api_url):
        self.api_key = api_key
        self.api_url = api_url
    def ListPeers(self):
        url = f"{self.api_url}/peers"

        headers = {
            'Accept': 'application/json',
            'Authorization': f'Token {self.api_key}'
        }
        response = requests.request("GET", url, headers=headers)
        return response.text

class Peer:
    def __init__(self, name, id, data):
        self.name = name
        self.id = id
        self.data = data
