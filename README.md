dominion_solutions.netbird
---
This collection allows you to manage your netbird servers.

- [Required Python Libraries](#required-python-libraries)
- [Roles](#roles)
  - [dominion\_solutions.netbird.netbird](#dominion_solutionsnetbirdnetbird)
- [Inventories](#inventories)
  - [dominion\_solutions.netbird.netbird](#dominion_solutionsnetbirdnetbird-1)
    - [Sample Inventory Setups](#sample-inventory-setups)
      - [Retrieve All Netbird Peers in the _Development_ group](#retrieve-all-netbird-peers-in-the-development-group)
      - [Retrieve all Netbird Peers that _are Connected_](#retrieve-all-netbird-peers-that-are-connected)
      - [A More Complex example](#a-more-complex-example)
    - [Available data for custom groupings](#available-data-for-custom-groupings)
- [Contributing](#contributing)
- [Contributors](#contributors)


# Required Python Libraries
- ansible ~=9.2.0
- requests ~=2.31.0 (If using the inventory plugin)

# Roles
## dominion_solutions.netbird.netbird
Applying this role will install the netbird client on the target machine.

[Documentation](https://galaxy.ansible.com/ui/repo/published/dominion_solutions/netbird/content/role/netbird/)

# Inventories
## dominion_solutions.netbird.netbird
This is a dynamic inventory generated based on the configuration in the netbird API.

[Documentation](https://galaxy.ansible.com/ui/repo/published/dominion_solutions/netbird/content/inventory/netbird/)

### Sample Inventory Setups
#### Retrieve All Netbird Peers in the _Development_ group
```yaml
---
plugin: dominion_solutions.netbird.netbird
api_url: https://api.netbird.io/api/
api_key: nbp_this_is_a_fake_api_key
netbird_groups:
  - Development
strict: No
```

#### Retrieve all Netbird Peers that _are Connected_
```yaml
---
plugin: dominion_solutions.netbird.netbird
api_key: nbp_this_is_a_fake_api_key
api_url: https://netbird.example.com/api/v1
netbird_connected: True
```

#### A More Complex example
This example gets all peers in the _All_ group and builds the additional _connected_ and _ssh\_hosts_ groups, based on the keys.
```yaml
---
plugin: dominion_solutions.netbird.netbird
api_key: nbp_this_is_a_fake_api_key
api_url: https://netbird.example.com/api/v1
netbird_connected: False
leading_separator: No
netbird_groups:
- "All"
groups:
  connected: connected
  ssh_hosts: ssh_enabled
strict: No
keyed_groups:
compose:
  ansible_ssh_host: label
  ansible_ssh_port: 22
```
### Available data for custom groupings
Fields are taken directly from the responses at the [Netbird Peers API](https://docs.netbird.io/api/resources/peers#list-all-peers) unless otherwise indicated

| Field                     | Type      | Notes |
| ------------------------- | --------- | ----- |
| label                     | `string`  | `label` is a field generated as part of the inventory as an alias to the `dns_label` field. |
| id                        | `string`  |       |
| name                      | `string`  |       |
| ip                        | `string`  |       |
| connected                 | `boolean` |       |
| last_seen                 | `string`  | This is is an [ISO-8601](https://en.wikipedia.org/wiki/ISO_8601) UTC Date Time String |
| os                        | `string`  | An OS Identifier such as `Linux Mint 21.3` or `Alpine Linux 3.19.1` |
| version                   | `string`  | The version of the Netbird Client that is running on the Peer |
| groups                    | `object`  | The groups object.  This is parsed into the the groups in the inventory by name.  |
| enabled                   | `boolean` |       |
| user_id                   | `string`  |       |
| hostname                  | `string`  | The hostname part of the FQDN |
| ui_version                | `string`  | Blank if there's no UI client installed, otherwise a version for the UI such as `netbird-desktop-ui/0.25.7` |
| dns_label                 | `string`  | The Fully Qualified Domain Name for this peer. |
| login_expiration_enabled  | `boolean` | Is this peer exempt from login expiration? |
| login_expired             | `boolean` | Is the login for this expired? |
| last_login                | `string`  |       |
| approval_required         | `boolean` |       |
| accessible_peers_count    | `integer` |       |

# Contributing
Please see [CONTRIBUTING.md](https://github.com/dominion-solutions/ansible-netbird/blob/main/.github/CONTRIBUTING.md)

# Contributors
- [Mark J. Horninger](https://github.com/spam-n-eggs)
- [All Contributors](https://github.com/dominion-solutions/ansible-netbird/graphs/contributors)
