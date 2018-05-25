# Unit tests
This directory contains a file (task list) for each custom Ansible filter
written in Python. These are the parsers used to transform CLI output (text)
from the network devices into structured data.

## Running tests
The playbook in the previous directory called `test_playbook.yml` includes
these task lists for execution. The tests are kept simple using static text
input with bogus values to ensure the parsers function correctly.

## Targeted testing
If you only want to run a subset of unit tests, you can override the `TASKS`
variable from the CLI using `-e` or `--extra-vars`. For example, to only test
the IOS OSPF neighbor functionality, use this command:

`ansible-playbook test_playbook.yml -e "TASKS=test_ios_ospf_neighbor.yml"`

Since this string is a regex, quantifiers are supported. For example, to only
test IOS-XR related filters, use this command:

`ansible-playbook test_playbook.yml -e "TASKS=test_iosxr*"`
