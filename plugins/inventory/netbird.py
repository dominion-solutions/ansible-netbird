# -*- coding: utf-8 -*-
# Copyright: (c) 2024, Dominion Solutions LLC (https://dominion.solutions) <sales@dominion.solutions>
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r"""
  name: netbird
  author: Mark J. Horninger (@spam-n-eggs)
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

from ansible.errors import AnsibleError

from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable

# Specific for the NetbirdAPI Class
import json
try:
    import requests
except ImportError:
    HAS_NETBIRD_API_LIBS = False
else:
    HAS_NETBIRD_API_LIBS = True


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):
    NAME = "dominion_solutions.netbird"

    def _build_client(self, loader):
        """Build the Netbird API Client"""

        api_key = self.get_option('api_key')
        api_url = self.get_option('api_url')
        if self.templar.is_template(api_key):
            api_key = self.templar.template(api_key)
        if self.templar.is_template(api_url):
            api_url = self.templar.template(api_url)

        if api_key is None:
            raise AnsibleError("Could not retrieve the Netbird API Key from the configuration sources.")
        if api_url is None:
            raise AnsibleError("Could not retrieve the Netbird API URL from the configuration sources.")

        self.client = NetbirdApi(api_key, api_url)

    def _get_peer_inventory(self):
        """Get the inventory from the Netbird API"""
        self.peers = self.client.ListPeers()

    def parse(self, inventory, loader, path, cache=True):
        """Dynamically parse the inventory from the Netbird API"""
        super(InventoryModule, self).parse(inventory, loader, path)
        if not HAS_NETBIRD_API_LIBS:
            raise AnsibleError("the Netbird Dynamic inventory requires Requests.")

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


# This is a very limited wrapper for the netbird API.
class NetbirdApi:
    def __init__(self, api_key, api_url):
        self.api_key = api_key
        self.api_url = api_url

    def ListPeers(self):
        """List all peers in the Netbird API

        Returns:
            peers: A list of Peer objects with the data.
        """
        url = f"{self.api_url}/peers"
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Token {self.api_key}'
        }
        peers = []
        response = requests.request("GET", url, headers=headers)
        peer_json = json.loads(response.text)
        for current_peer_map in peer_json:
            current_peer = Peer(current_peer_map["hostname"], current_peer_map["id"], current_peer_map)
            peers.append(current_peer)
        return peers


class Peer:
    # This is an example peers response from the Netbird API:
    # [
    #   {
    #     "accessible_peers_count": 1,
    #     "approval_required": false,
    #     "connected": false,
    #     "dns_label": "apple.netbird.cloud",
    #     "groups": [
    #       {
    #         "id": "2a3b4c5d6e7f8g9h0i1j",
    #         "name": "All",
    #         "peers_count": 2
    #       }
    #     ],
    #     "hostname": "apple",
    #     "id": "3a7b2c1d4e5f6g8h9i0j",
    #     "ip": "100.0.0.42",
    #     "last_login": "2024-02-10T22:01:27.744131502Z",
    #     "last_seen": "2024-02-11T03:21:42.202104672Z",
    #     "login_expiration_enabled": true,
    #     "login_expired": false,
    #     "name": "apple",
    #     "os": "Linux Mint 21.3",
    #     "ssh_enabled": false,
    #     "ui_version": "netbird-desktop-ui/0.25.7",
    #     "user_id": "auth0|ABC123xyz4567890",
    #     "version": "0.25.7"
    #   },
    #   {
    #     "accessible_peers_count": 1,
    #     "approval_required": false,
    #     "connected": true,
    #     "dns_label": "banana.netbird.cloud",
    #     "groups": [
    #       {
    #         "id": "2a3b4c5d6e7f8g9h0i1j",
    #         "name": "All",
    #         "peers_count": 2
    #       }
    #     ],
    #     "hostname": "banana",
    #     "id": "3a7b2c1d4e5f6g8h9i0j",
    #     "ip": "100.0.0.61",
    #     "last_login": "2024-02-02T11:20:05.934889112Z",
    #     "last_seen": "2024-02-16T16:14:35.853243309Z",
    #     "login_expiration_enabled": false,
    #     "login_expired": false,
    #     "name": "banana",
    #     "os": "Alpine Linux 3.19.1",
    #     "ssh_enabled": false,
    #     "ui_version": "",
    #     "user_id": "",
    #     "version": "0.25.5"
    #   }
    # ]

    def __init__(self, name, id, data):
        self.name = name
        self.id = id
        self.data = data
