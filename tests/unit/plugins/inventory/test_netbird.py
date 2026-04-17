# -*- coding: utf-8 -*-
# Copyright 2024 Dominion Solutions LLC <sales@dominion.solutions> (https://dominion.solutions)
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible.errors import AnsibleError
from ansible.inventory.data import InventoryData
from ansible.parsing.dataloader import DataLoader
from ansible.template import Templar
from ansible.utils.display import Display

from ansible_collections.dominion_solutions.netbird.plugins.inventory.netbird import InventoryModule, NetbirdApi, Peer

from unittest.mock import MagicMock
import json

display = Display()


@pytest.fixture(scope="module")
def inventory():
    plugin = InventoryModule()
    plugin.templar = Templar(loader=DataLoader())
    plugin._redirected_names = ["netbird", "dominion_solutions.netbird.netbird"]
    plugin._load_name = plugin.NAME
    return plugin


@pytest.fixture(scope="module")
def netbird_api():
    mock_netbird_api = NetbirdApi(None, None)
    response_data = []
    with open('tests/unit/module_utils/inventories/fixtures/peers.json') as peers_file:
        peers_map = json.load(peers_file)
        for data in peers_map:
            response_data.append(Peer(data['hostname'], data['dns_label'], data['id'], data))

    mock_netbird_api.ListPeers = MagicMock(return_value=response_data)

    return mock_netbird_api


@pytest.fixture(scope="module")
def netbird_api_multigroup():
    mock_netbird_api = NetbirdApi(None, None)
    response_data = []
    with open('tests/unit/module_utils/inventories/fixtures/peers_multigroup.json') as peers_file:
        peers_map = json.load(peers_file)
        for data in peers_map:
            response_data.append(Peer(data['hostname'], data['dns_label'], data['id'], data))

    mock_netbird_api.ListPeers = MagicMock(return_value=response_data)

    return mock_netbird_api


@pytest.fixture(scope="module")
def netbird_api_spaces_in_group():
    mock_netbird_api = NetbirdApi(None, None)
    response_data = []
    with open('tests/unit/module_utils/inventories/fixtures/peers_spaces_in_group.json') as peers_file:
        peers_map = json.load(peers_file)
        for data in peers_map:
            response_data.append(Peer(data['hostname'], data['dns_label'], data['id'], data))

    mock_netbird_api.ListPeers = MagicMock(return_value=response_data)

    return mock_netbird_api


@pytest.fixture(scope="module")
def netbird_api_with_users():
    mock_netbird_api = NetbirdApi(None, None)
    peers_data = []
    with open('tests/unit/module_utils/inventories/fixtures/peers_with_users.json') as peers_file:
        peers_map = json.load(peers_file)
        for data in peers_map:
            peers_data.append(Peer(data['hostname'], data['dns_label'], data['id'], data))

    with open('tests/unit/module_utils/inventories/fixtures/users.json') as users_file:
        users_data = json.load(users_file)

    mock_netbird_api.ListPeers = MagicMock(return_value=peers_data)
    mock_netbird_api.ListUsers = MagicMock(return_value=users_data)

    return mock_netbird_api


def test_missing_access_token_lookup(inventory):
    loader = DataLoader()
    inventory._options = {'api_key': None, 'api_url': None}
    with pytest.raises(AnsibleError) as error_message:
        inventory._build_client(loader)
        assert 'Could not retrieve Netbird access token' in error_message


def test_verify_file(tmp_path, inventory):
    file = tmp_path / "foobar.netbird.yml"
    file.touch()
    assert inventory.verify_file(str(file)) is True


def test_verify_file_bad_config(inventory):
    assert inventory.verify_file('foobar.netbird.yml') is False


def test_get_peer_data(inventory, netbird_api):
    loader = DataLoader()
    path = 'tests/unit/module_utils/inventories/fixtures/netbird.yml'
    inventory._build_client = MagicMock()
    inventory.client = netbird_api
    inventory.parse(InventoryData(), loader, path, False)
    assert inventory.inventory is not None
    assert inventory.inventory.hosts is not None
    assert len(inventory.inventory.groups.get('ssh_hosts').hosts) == 2
    assert len(inventory.inventory.groups.get('connected').hosts) == 1


def test_get_only_connected_peers(inventory, netbird_api):
    loader = DataLoader()
    path = 'tests/unit/module_utils/inventories/fixtures/only_connected.netbird.yml'
    inventory._build_client = MagicMock()
    inventory.client = netbird_api
    inventory.parse(InventoryData(), loader, path, False)
    assert inventory.inventory is not None
    assert inventory.inventory.hosts is not None
    assert len(inventory.inventory.hosts) == 1
    assert list(inventory.inventory.hosts.values())[0].get_vars().get('connected') is True


def test_with_multiple_groups(inventory, netbird_api_multigroup):
    loader = DataLoader()
    path = 'tests/unit/module_utils/inventories/fixtures/only_connected.netbird.yml'
    inventory._build_client = MagicMock()
    inventory.client = netbird_api_multigroup
    inventory.parse(InventoryData(), loader, path, False)
    assert inventory.inventory is not None
    assert inventory.inventory.hosts is not None
    assert inventory.inventory.groups is not None
    assert 'All' in inventory.inventory.groups
    assert 'Development' in inventory.inventory.groups


def test_with_multiple_groups(inventory, netbird_api_multigroup):
    loader = DataLoader()
    path = 'tests/unit/module_utils/inventories/fixtures/only_connected.netbird.yml'
    inventory._build_client = MagicMock()
    inventory.client = netbird_api_multigroup
    inventory.parse(InventoryData(), loader, path, False)
    assert inventory.inventory is not None
    assert inventory.inventory.hosts is not None
    assert inventory.inventory.groups is not None
    assert 'All' in inventory.inventory.groups
    assert 'Development' in inventory.inventory.groups


def test_use_ip_address(inventory, netbird_api_multigroup):
    loader = DataLoader()
    path = 'tests/unit/module_utils/inventories/fixtures/ip_address.netbird.yml'
    inventory._build_client = MagicMock()
    inventory.client = netbird_api_multigroup
    inventory.parse(InventoryData(), loader, path, False)
    assert inventory.inventory is not None
    assert inventory.inventory.hosts is not None
    assert inventory.inventory.groups is not None
    assert 'All' in inventory.inventory.groups
    assert 'Development' in inventory.inventory.groups


def test_use_group_with_spaces(inventory, netbird_api_spaces_in_group):
    loader = DataLoader()
    path = 'tests/unit/module_utils/inventories/fixtures/spaces_in_group.netbird.yml'
    inventory._build_client = MagicMock()
    inventory.client = netbird_api_spaces_in_group
    inventory.parse(InventoryData(), loader, path, False)
    assert inventory.inventory is not None
    assert inventory.inventory.hosts is not None
    assert inventory.inventory.groups is not None
    assert 'All' in inventory.inventory.groups
    assert 'Test Group With Spaces' in inventory.inventory.groups


def test_list_user_peers(inventory, netbird_api_with_users):
    """Test that list_user_peers creates user-based groups with peers."""
    loader = DataLoader()
    path = 'tests/unit/module_utils/inventories/fixtures/list_user_peers.netbird.yml'
    inventory._build_client = MagicMock()
    inventory.client = netbird_api_with_users
    inventory.parse(InventoryData(), loader, path, False)

    assert inventory.inventory is not None
    assert inventory.inventory.hosts is not None
    assert inventory.inventory.groups is not None

    # Check that user groups were created (service user excluded by default)
    assert 'user_john_doe' in inventory.inventory.groups
    assert 'user_jane_smith' in inventory.inventory.groups
    # Service user should NOT be included when include_service_users is False
    assert 'user_ci_cd_service_account' not in inventory.inventory.groups

    # Check that John Doe has 2 peers
    john_group = inventory.inventory.groups.get('user_john_doe')
    assert john_group is not None
    assert len(john_group.hosts) == 2

    # Check that Jane Smith has 1 peer
    jane_group = inventory.inventory.groups.get('user_jane_smith')
    assert jane_group is not None
    assert len(jane_group.hosts) == 1

    # Verify hostvars contain user information
    laptop_john_host = inventory.inventory.get_host('laptop-john.netbird.cloud')
    assert laptop_john_host is not None
    laptop_vars = laptop_john_host.get_vars()
    assert laptop_vars.get('user_email') == 'john.doe@example.com'
    assert laptop_vars.get('user_name') == 'John Doe'
    assert laptop_vars.get('user_role') == 'admin'
    assert laptop_vars.get('user_is_service_user') is False
    # Verify the IP is accessible
    assert laptop_vars.get('ip') == '100.64.0.1'


def test_list_user_peers_with_service_users(inventory, netbird_api_with_users):
    """Test that list_user_peers includes service users when enabled."""
    loader = DataLoader()
    path = 'tests/unit/module_utils/inventories/fixtures/list_user_peers_with_service.netbird.yml'
    inventory._build_client = MagicMock()
    inventory.client = netbird_api_with_users
    inventory.parse(InventoryData(), loader, path, False)

    assert inventory.inventory is not None
    assert inventory.inventory.groups is not None

    # Check that all user groups were created including service user
    assert 'user_john_doe' in inventory.inventory.groups
    assert 'user_jane_smith' in inventory.inventory.groups
    assert 'user_ci_cd_service_account' in inventory.inventory.groups

    # Check that service user group has the CI runner peer
    service_group = inventory.inventory.groups.get('user_ci_cd_service_account')
    assert service_group is not None
    assert len(service_group.hosts) == 1

    # Verify service user hostvars
    ci_runner_host = inventory.inventory.get_host('ci-runner.netbird.cloud')
    assert ci_runner_host is not None
    ci_vars = ci_runner_host.get_vars()
    assert ci_vars.get('user_is_service_user') is True
    assert ci_vars.get('ip') == '100.64.0.100'
