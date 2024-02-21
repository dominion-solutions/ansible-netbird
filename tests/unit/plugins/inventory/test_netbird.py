# -*- coding: utf-8 -*-
# Copyright 2024 Dominion Solutions LLC <sales@dominion.solutions> (https://dominion.solutions)
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest


# TODO: Reenable this if needed.
# import sys

from ansible.errors import AnsibleError
from ansible.parsing.dataloader import DataLoader
from ansible.template import Templar
from ansible_collections.dominion_solutions.netbird.plugins.inventory.netbird import InventoryModule, NetbirdApi, Peer
from ansible.utils.display import Display
from unittest.mock import MagicMock
import json

display = Display()

@pytest.fixture(scope="module")
def inventory():
    plugin = InventoryModule()
    plugin.templar = Templar(loader=DataLoader())
    return plugin


@pytest.fixture(scope="module")
def netbird_api():
    mock_netbird_api = NetbirdApi(None, None)
    response_data = []
    with open('tests/unit/module_utils/inventories/fixtures/peers.json') as peers_file:
        peers_map = json.load(peers_file)
        for data in peers_map:
            response_data.append(Peer(data['hostname'], data['id'], data))

    mock_netbird_api.ListPeers = MagicMock(return_value=response_data)

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
    inventory.parse(dict(), loader, path, False)
    assert inventory.inventory is not None
    raise AnsibleError(inventory.inventory)