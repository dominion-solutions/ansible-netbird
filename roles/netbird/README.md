Role Name
=========
A role that installs the very basic version of Netbird, utilizing their install scripts.

Requirements
------------
- curl

Role Variables
--------------
- `netbird_setup_key`: The key that is used to automate the setup process.
- `netbird_register`: A true/false defining whether or not register netbird.
- `netbird_mgmt_url`: The management URL for the self-hosted instance. If not specified, defaults to the cloud-hosted instance (https://api.netbird.io:443).

Dependencies
------------
- None

Example Playbook
----------------
```yml
---
- name: Install Netbird
  hosts: localhost
  become: true
  vars:
    netbird_setup_key: "{{ lookup('env', 'NETBIRD_SETUP_KEY') }}"
    netbird_register: true
  tasks:
    - name: Check for netbird setup key
      ansible.builtin.fail:
        msg: "netbird_setup_key is required"
      when: netbird_setup_key is not defined

    - name: Install Netbird
      ansible.builtin.include_role:
        name: netbird

    - name: Check Netbird Status
      ansible.builtin.shell: |
        netbird status --detail
```

License
-------
MIT

Author Information
------------------
- Mark J. Horninger <sales@dominion.solutions>
- Many thanks to [Benjamin Arntzen](https://github.com/Zorlin) for his role that served as a guideline to build this role.
