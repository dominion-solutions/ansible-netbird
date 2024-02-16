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
from ansible_collections.dominion_solutions.netbird.plugins.inventory.netbird import InventoryModule


@pytest.fixture(scope="module")
def inventory():
    plugin = InventoryModule()
    plugin.templar = Templar(loader=DataLoader())
    return plugin


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
