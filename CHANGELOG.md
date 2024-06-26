# Changelog

All notable changes to this project will be documented in this file.

## Bug Fixes - Parameters - 2024-04-03

### Bug Fixes

Thanks to @ipsecguy for pointing out that there was an issue with the compose variables.

- #28 - The compose parameter is updated to accept a `dict()` now.
- The documentation has been improved as well.
- Some small issues around creating bugs / questions have been resolved.

### What's Changed

* Update README.md by @spam-n-eggs in https://github.com/dominion-solutions/ansible-netbird/pull/26
* Fixes #28 - Tested with a separate inventory. by @spam-n-eggs in https://github.com/dominion-solutions/ansible-netbird/pull/29

**Full Changelog**: https://github.com/dominion-solutions/ansible-netbird/compare/0.1.6...0.2.0

## Fixed an accidental bug in the last release - 2024-03-11

Bug was accidentally released in the last release.  Fixed.

### What's Changed

* Mjh/fix issues with message by @spam-n-eggs in https://github.com/dominion-solutions/ansible-netbird/pull/24

**Full Changelog**: https://github.com/dominion-solutions/ansible-netbird/compare/0.1.5...0.1.6

## Small Bugfixes - 2024-03-11

Minor fixes including:

- #14 Error on bad credentials.
- #22 Wrapped bad urls in an AnsibleError
- #20 The issue templates were bad.

### What's Changed

* Mjh/14/error out on bad credentials by @spam-n-eggs in https://github.com/dominion-solutions/ansible-netbird/pull/23

**Full Changelog**: https://github.com/dominion-solutions/ansible-netbird/compare/0.1.4...0.1.5

## Documentation updates - 2024-03-01

Closes #16

### What's Changed

* Updated Readme in a big way. by @spam-n-eggs in https://github.com/dominion-solutions/ansible-netbird/pull/17

**Full Changelog**: https://github.com/dominion-solutions/ansible-netbird/compare/0.1.3...0.1.4

## Securtity Vulnerability Fixes - 2024-02-24

Fixes security vulnerabilities

### What's Changed

* Bump cryptography from 42.0.2 to 42.0.4 by @dependabot in https://github.com/dominion-solutions/ansible-netbird-role/pull/9
* 'Fixed' Galaxy commit step by @spam-n-eggs in https://github.com/dominion-solutions/ansible-netbird-role/pull/10
* updated the steps to the galaxy.yml update gets included. by @spam-n-eggs in https://github.com/dominion-solutions/ansible-netbird-role/pull/11

### New Contributors

* @dependabot made their first contribution in https://github.com/dominion-solutions/ansible-netbird-role/pull/9

**Full Changelog**: https://github.com/dominion-solutions/ansible-netbird-role/compare/0.1.2...0.1.3

## Security Vulnerability Fixes - 2024-02-24

Fixes security vulnerabilities

### What's Changed

* Bump cryptography from 42.0.2 to 42.0.4 by @dependabot in https://github.com/dominion-solutions/ansible-netbird-role/pull/9
* 'Fixed' Galaxy commit step by @spam-n-eggs in https://github.com/dominion-solutions/ansible-netbird-role/pull/10

### New Contributors

* @dependabot made their first contribution in https://github.com/dominion-solutions/ansible-netbird-role/pull/9

**Full Changelog**: https://github.com/dominion-solutions/ansible-netbird-role/compare/0.1.2...0.1.3

## [Bug] Not all groups being found - 2024-02-24

This release fixes a critical bug where not all groups were being found during the list comprehension that was finding all of the groups.

### What's Changed

* Fixed issues with the groups list comprehension by @spam-n-eggs in https://github.com/dominion-solutions/ansible-netbird-role/pull/8

**Full Changelog**: https://github.com/dominion-solutions/ansible-netbird-role/compare/0.1.1...0.1.2
