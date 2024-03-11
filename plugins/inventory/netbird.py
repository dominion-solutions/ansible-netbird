# -*- coding: utf-8 -*-
# netbird inventory Ansible plugin
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
        choices: ['netbird', 'dominion_solutions.netbird.netbird']
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
    netbird_groups:
        description: A list of Netbird groups to filter the inventory by.
        type: list
        required: False
        elements: string
    netbird_connected:
        description: Filter the inventory by connected peers.
        default: True
        type: boolean
    strict:
        description: Whether or not to fail if a group or variable is not found.
    compose:
        description: compose variables for Ansible based on jinja2 expression and inventory vars
        default: False
        required: False
        type: boolean
    keyed_groups:
        description: create groups for plugins based on variable values and add the corresponding hosts to it
        type: list
        required: False
'''

EXAMPLES = r"""
# This is an inventory that finds the All Group and creates groups for the connected and ssh_enabled peers.
---
plugin: dominion_solutions.netbird.netbird
api_key: << api_key >>
api_url: << api_url >>
netbird_groups:
- "All"
groups:
  connected: connected
  ssh_hosts: ssh_enabled
strict: No
compose:
  ansible_ssh_host: label
  ansible_ssh_port: 22

"""

from ansible.errors import AnsibleError

from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable
from ansible.utils.display import Display

# Specific for the NetbirdAPI Class
import json
import re

try:
    import requests
except ImportError:
    HAS_NETBIRD_API_LIBS = False
else:
    HAS_NETBIRD_API_LIBS = True

display = Display()


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):
    NAME = "dominion_solutions.netbird.netbird"

    def _cacheable_inventory(self):
        return [p._raw_json for p in self.peers]

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
                group.get('name') for peer
                in self.peers
                for group in
                peer.data.get('groups')
            ]))
        for group in self.netbird_groups:
            self.inventory.add_group(group)

    def _add_peers_to_group(self):
        """ Add peers to the groups in the inventory. """
        for peer in self.peers:
            for group in peer.data.get("groups"):
                self.inventory.add_host(peer.label, group=group.get('name'))

    def _get_peer_inventory(self):
        """Get the inventory from the Netbird API"""
        try:
            self.peers = self.client.ListPeers()
        except Exception:
            raise AnsibleError(f"Could not retrieve the Netbird inventory.  Check the API Key and URL.")

    def _filter_by_config(self):
        """Filter peers by user specified configuration."""
        connected = self.get_option('netbird_connected')
        groups = self.get_option('netbird_groups')
        if connected:
            self.peers = [
                peer for peer in self.peers if peer.data.get('connected')
            ]
        if groups:
            self.peers = [
                # 202410221 MJH:  This list comprehension that  filters the peers is a little hard to read.  I'm sorry.
                # If you can fix it and make it more readable, please feel free to make a PR.
                peer for peer in self.peers
                if any(
                    group
                    in [
                        # Emulate a pluck here to grab the group names from the peer data.
                        g.get('name') for g in peer.data.get('groups')
                    ]
                    for group in groups)
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
                    peer.label,
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
            self._build_client(loader)
            self._get_peer_inventory()

        if update_cache:
            self._cache[cache_key] = self._cacheable_inventory()

        self.populate()

    def populate(self):
        """ Populate the inventory with the peers from the Netbird API. """
        strict = self.get_option('strict')

        self._filter_by_config()

        self._add_groups()
        self._add_peers_to_group()
        self._add_hostvars_for_peers()

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
        if response.status_code in [401, 404]:
            raise Exception(f"{response.status_code}: {response.text}\nPlease check the API Key and URL.")

        peer_json = json.loads(response.text)
        for current_peer_map in peer_json:
            current_peer = Peer(current_peer_map["hostname"], current_peer_map['dns_label'], current_peer_map["id"], current_peer_map)
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

    def __init__(self, name, label, id, data):
        self.name = name
        self.label = label
        self.id = id
        self.data = data
