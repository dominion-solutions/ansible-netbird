# -*- coding: utf-8 -*-
# Copyright: (c) 2024, Dominion Solutions LLC (https://dominion.solutions) <sales@dominion.solutions>
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
name: netbird
author: Mark J. Horninger (@spam-n-eggs)
version_added: 0.0.2
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
    plugin:
        description: Marks this as an instance of the 'netbird' plugin.
        required: true
        choices: ['netbird', 'dominion_solutions.netbird']
    ip_style:
        description: Populate hostvars with all information available from the Netbird API.
        type: string
        default: plain
        choices:
            - plain
            - api
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
    include_disconnected:
        description: Whether or not to include disconnected peers in the inventory
        type: boolean
        default: false
'''

EXAMPLES = r"""
"""

from ansible.errors import AnsibleError

from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable
from ansible.utils.display import Display

# Specific for the NetbirdAPI Class
import json

try:
    import requests
except ImportError:
    HAS_NETBIRD_API_LIBS = False
else:
    HAS_NETBIRD_API_LIBS = True

display = Display()


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):
    NAME = "dominion_solutions.netbird"

    _redirected_names = ["netbird", "dominion_solutions.netbird"]

    _load_name = NAME

    def _build_client(self, loader):
        """Build the Netbird API Client"""
        display.v("Building the Netbird API Client.")
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

        display.v(f"Set up the Netbird API Client with the URL: {api_url}")
        self.client = NetbirdApi(api_key, api_url)

    def _add_groups(self):
        """ Add peer groups to the inventory. """
        self.netbird_groups = set(
            filter(None, [
                peer.data.get("groups")
                for peer
                in self.peers
            ])
        )
        for group in self.netbird_groups:
            self.inventory.add_group(group)

    def _add_peers_to_group(self):
        """ Add peers to the groups in the inventory. """
        for peer in self.peers:
            for group in peer.data.get("groups"):
                self.inventory.add_host(peer.name, group=group)

    def _get_peer_inventory(self):
        """Get the inventory from the Netbird API"""
        if self.include_disconnected is False:
            self.peers = [peer for peer in self.client.ListPeers() if peer.data["connected"] is True]
        else:
            display.vv("Including disconnected peers.")
            self.peers = self.client.ListPeers()

    def _filter_by_config(self):
        """Filter peers by user specified configuration."""
        groups = self.get_option('groups')
        if groups:
            self.peers = [
                peer for peer in self.peers
                if any(group in peer.data['groups'] for group in groups)
            ]

    def _add_hostvars_for_peers(self):
        """Add hostvars for peers in the dynamic inventory."""
        ip_style = self.get_option('ip_style')
        for peer in self.peers:
            hostvars = peer._raw_json
            for hostvar_key in hostvars:
                if ip_style == 'api' and hostvar_key in ['ip', 'ipv6']:
                    continue
                self.inventory.set_variable(
                    peer.name,
                    hostvar_key,
                    hostvars[hostvar_key]
                )
            if ip_style == 'api':
                ips = peer.ips.ipv4.public + peer.ips.ipv4.private
                ips += [peer.ips.ipv6.slaac, peer.ips.ipv6.link_local]
                ips += peer.ips.ipv6.pools

                for ip_type in set(ip.type for ip in ips):
                    self.inventory.set_variable(
                        peer.label,
                        ip_type,
                        self._ip_data([ip for ip in ips if ip.type == ip_type])
                    )

    def verify_file(self, path):
        """Verify the Linode configuration file."""
        if super(InventoryModule, self).verify_file(path):
            endings = ('netbird.yaml', 'netbird.yml')
            if any((path.endswith(ending) for ending in endings)):
                return True
        return False

    def parse(self, inventory, loader, path, cache=True):
        """Dynamically parse the inventory from the Netbird API"""
        super(InventoryModule, self).parse(inventory, loader, path)
        if not HAS_NETBIRD_API_LIBS:
            raise AnsibleError("the Netbird Dynamic inventory requires Requests.")

        self._options = self._read_config_data(path)
        self.peers = None

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
        # for empty sets of cached peers
        if self.peers is None:
            self.include_disconnected = self.get_option('include_disconnected')
            self._build_client(loader)
            self._get_peer_inventory()
            self._add_hostvars_for_peers()


        if update_cache:
            self._cache[cache_key] = self._cacheable_inventory()

        self.populate()

    def populate(self):
        self._filter_by_config()
        self._add_groups()
        self._add_peers_to_group()


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
    @property
    def _raw_json(self):
        return self.data

    def __init__(self, name, id, data):
        self.name = name
        self.id = id
        self.data = data
