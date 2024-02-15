from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r"""
  name: netbird
  author:
  - Mark Horninger (@dominion.soltuions@mstdn.business) <mark.horninger@dominion.solutions>
  version_added: "0.0.2"
  requirements:
    - requests>=2.31.0
  short_description: Get inventory from the Netbird API
  description:
    - Get inventory from the Netbird API.  Allows for filtering based on Netbird Tags / Groups.
  extends_documentation_fragment:
    - constructed
    - inventory_cache
  options:
    cache:
        description: Cache plugin output to a file
        type: boolean
        default: true
    cache_plugin:
        description: Cache plugin to use for the inventory's cache
        type: string
        default: jsonfile
        choices: ['memory', 'jsonfile', 'yaml', 'together', 'redis']
    cache_connectoin:
        description: Connection information for the cache plugin
        type: string
        default: None
    cache_prefix:
        description: Prefix to use for cache plugin files/tables
        type: string
        default: ANSIBLE_
    plugin:
        description: Marks this as an instance of the 'netbird' plugin.
        required: true
        choices: ['netbird', 'dominion_solutions.netbird']
    api_key:
      description: The API Key for the Netbird API.
      required: true
      type: string
      env:
        - name: NETBIRD_API_KEY
    api_url:
      description: The URL for the Netbird API.
      required: true
      type: string
      env:
        - name: NETBIRD_API_URL
    strict:
        description: If true make invalid entries a fatal error, otherwise skip and continue
        type: boolean
        default: false
    compose:
        description: Whether or not to create composed groups based on the variables of the hosts
        type: boolean
        default: false
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

    def _build_client(self, loader):
        """Build the Netbird API Client"""

        access_token = self.get_option('api_key')
        api_url = self.get_option('api_url')
        if self.templar.is_template(access_token):
            access_token = self.templar.template(access_token)
        if self.templar.is_template(api_url):
            api_url = self.templar.template(api_url)

        if access_token is None:
            raise AnsibleError("Could not retrieve the Netbird API Key from the configuration sources.")
        if api_url is None:
            raise AnsibleError("Could not retrieve the Netbird API URL from the configuration sources.")

        self.client = NetbirdApi(access_token, api_url)

    def _get_peer_inventory(self):
        """Get the inventory from the Netbird API"""
        self.peers = self.client.ListPeers()

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

    def populate(self):
        strict = self.get_option('strict')

        self._filter_by_config()

        self._add_groups()
        self._add_instances_to_groups()
        self._add_hostvars_for_instances()
        for peer in self.peers:
            variables = self.inventory.get_host(peer.label).get_vars()
            self._add_host_to_composed_groups(
                self.get_option('groups'),
                variables,
                peer.label,
                strict=strict)
            self._add_host_to_keyed_groups(
                self.get_option('keyed_groups'),
                variables,
                peer.label,
                strict=strict)
            self._set_composite_vars(
                self.get_option('compose'),
                variables,
                peer.label,
                strict=strict)

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
