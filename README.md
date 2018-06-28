[![Build Status](
https://travis-ci.org/nickrusso42518/nots.svg?branch=master)](
https://travis-ci.org/nickrusso42518/nots)

# Nick's OSPF TroubleShooter (nots)
A simple but powerful Ansible playbook to troubleshoot OSPF network problems
on a variety of platforms. It is simple because it does not require
extensive preparatory configuration for individual host state checking.
It is powerful because despite not having the aforementioned level of
granularity, it rapidly discovers the vast majority of OSPF problems.

> Contact information:\
> Email:    njrusmc@gmail.com\
> Twitter:  @nickrusso42518

  * [Supported platforms](#supported-platforms)
  * [Summarized-test cases](#summarzed-test-cases)
  * [Variables](#variables)
  * [Logging](#logging)
  * [FAQ](#faq)

## Supported platforms
Today, Cisco IOS/IOS-XE, IOS-XR, and NX-OS are supported. Valid `device_type`
options used for inventory groups are enumerated below. Each platform
has a folder in the `devices/` directory, such as `devices/ios/`. The
file named `main.yml` is the task list that is included from the main
playbook which begins the device-specific tasks.

  * `ios`: Cisco classic IOS and Cisco IOS-XE devices.
  * `iosxr`: Cisco IOS-XR devices.
  * `nxos`: Cisco NX-OS devices.

Testing was conducted on the following platforms and versions:
  * Cisco CSR1000v, version 16.07.01a, running in AWS
  * Cisco XRv9000, version 6.3.1, running in AWS
  * Cisco 3172T, version 6.0.2.U6.4a, hardware appliance

Control machine information:
```
$ cat /etc/redhat-release
Red Hat Enterprise Linux Server release 7.4 (Maipo)

$ uname -a
Linux ip-10-125-0-100.ec2.internal 3.10.0-693.el7.x86_64 #1 SMP
  Thu Jul 6 19:56:57 EDT 2017 x86_64 x86_64 x86_64 GNU/Linux

$ ansible --version
ansible 2.4.3.0
  config file = /etc/ansible/ansible.cfg
  configured module search path = [u'/usr/share/my_modules']
  ansible python module location = /usr/lib/python2.7/site-packages/ansible
  executable location = /usr/bin/ansible
  python version = 2.7.5 (default, May  3 2017, 07:55:04)
    [GCC 4.8.5 20150623 (Red Hat 4.8.5-14)]
```

## Summarized test cases
The following tests are run in sequence. Note that the exact items tested
varies between platforms since command outputs and feature sets also vary.
Administrative tasks, such as creating directories and logging on the control
machine, are not detailed here for brevity.

### Per device testing
Ansible logs into each OSPF router for the purpose of collecting information
and validating its correctness based on a small amount of pre-identified
state configuration. As discussed in the "variables" section, some of these
tests can be skipped by modifying the appropriate key/value pairs.

The list of tests run on each specific device are enumerated under each
`README.md` file inside the subdirectories of `devices/` correlating to
each unique device type.

### Whole network testing
After individual routers are validated, additional tests based on the
aggregated data from all routers are run. It is possible to run these
tests on a per-host basis, but that would effectively cause the same test
to be run N times rather than one time.

  * Ensure there are no duplicate OSPF router IDs. While it is technically
    possible to duplicate RIDs in different areas (sometimes), there is no
    legitimate reason to do it. This playbook __always__ considers this
    condition an error.

## Variables
The following subsections detail the different types of variables, their
scopes, and their purposes within the playbook.

### Process-level
This playbook assumes that all OSPF routers are in a single process, and
if they are not, only a single process can be checked at a time.

Process-level variables differ between device types. For a list of supported
process variables, reference the individual `README.md` files in each
`devices/` subdirectory correlated to each device type.

### Area-level
This playbook allows an unlimited number of areas to be specified, each with
their own area-specific configuration. The playbook assumes that there are
no duplicate areas in the network. For example, while it is possible to have
two disparate area 1 sections of the network tied into area 0, this playbook
does not support it.

The top-level key is the area ID, specified as a string in the format
`"area#"` where # is the ID itself. For example: `"area0"` and `"area51"`

  * `type`: The area type, specified as a string from the following options:
    `"standard"`, `"nssa"`, `"stub"`. No other options are allowed, and
    area 0 __must__ be type `"standard"`. __This key is mandantory.__
  * `routers`: The number of routers expected to exist in a given area,
    expressed as a positive integer. To disable this check, exclude this key.
  * `drs`: The number of designated routers expected to exist in a given area,
    expressed as a positive integer. Note that DRs exist on broadcast-style
    network segments only, and are unnecessary on point-to-point links over
    broadcast media such as ethernet. To disable this check, exclude this key.
  * `has_frr`: Boolean representing whether OSPF Fast Re-Route
    (also known as Loop Free Alternative/LFA) should be enabled
    (`true`) or disabled (`false`) for this process. This test checks for the
    basic enablement (or not) of this feature and not advanced derivates, such
    as remote LFA (rLFA) or topology-independent LFA (TI-LFA).
    To disable this check, exclude this key.
  * `max_lsa3`: The maximum number of summary LSAs (LSA type-3) that should be
    present within an area. This inclusive upper bound enforces a limit on
    the number of LSA3 for the purpose of flood reduction and memory
    consumption. It can also enforce specific architectural designs. For
    example, a totally stubby area with one ABR has only one LSA3 for the
    default route, and this option can enforce this. This key is processed
    for any area type. To disable this check, exclude this key.
  * `max_lsa7`: The maximum number of NSSA-external LSAs (LSA type-7) that
    should be present within an area. This inclusive upper bound enforces a
    limit on the number of LSA7 for the purpose of flood reduction and memory
    consumption. It can also enforce specific architectural designs. For
    example, an extranet NSSA acting as a non-transit buffer might be receiving
    a small number of routes from a peer, which can be enforced. This key is
    only process when the area type is "nssa".
    To disable this check, exclude this key.

### Device group level
Each device type (`ios`, `iosxr`, etc.) has its own `group_vars/` file which
contains OS-specific parameters. __These should never be changed by consumers
as their main purpose is abstraction, not user input.__

  * `device_type`: A string representing the device OS name. These were
    enumerated in the "Supported Platforms" section earlier in the document.
  * `commands`: A list of strings representing the CLI commands to be
    issued to the device. These collect information from the devices relevant
    to troubleshooting OSPF.

Note that some extra commands are appended to the end of the `commands` list
which are used for collection only. The output from these commands is written
to the host log which can assist with troubleshooting, but it is not parsed
or checked in any way within the logic of the playbook.

### Host level
This playbook aims to minimize the number of host-specific variables as
managing these inventory variables becomes burdensome in large networks.

  * `my_areas`: List of integers representing the areas in which a given router
    participates. For example, a router only in area 0 would use `[0]`. A
    router in area 0 and 51 would use `[0, 51]`. Note that the playbook is
    smart enough to identify whether a router is an Area Border Router (ABR)
    or not based on its area membership. The empty list `[]` is not valid
    since all OSPF routers must belong to at least one area.
    __This key is mandantory.__
  * `my_nbr_count`: Number of neighbors a specific router is expected to have.
    This is the grand total of all OSPF neighbors in a given process and is
    not checked on a per-interface or per-area basis. It is a positive
    integer. To disable this check, exclude this key. Disabling this check on
    routers with a variable number of neighbors, such as an Internet VPN
    concentrator, could be useful.
  * `should_be_asbr`: Boolean representing whether a router should be an
    Autonomous System Boundary Router (ASBR). A value of `true` indicates
    that a router should be an ASBR (note that this includes NSSA ABRs)
    and a value of `false` indicates that a router should not be an ASBR.
    To disable this check, exclude this key.
  * `should_be_stub_rtr`: Boolean representing whether a router should be a
    stub router with max-metric advertised for all links. This reduces the
    likelihood that a router is used for transit. A value of `true` indicates
    that a router should be a stub router (minor options are not evaluated)
    and a value of `false` indicates that a router should not be a stub router.
    To disable this check, exclude this key.

## Logging
Given the generic nature of the playbook, some tests will fail with generic
error messages. For example, one host may fail because a router had an
incorrect number of actual neighbors, either greater than or less than
the user-configured `my_nbr_count` expectation. By design, the playbook
lacks granularity to determine which neighbor failed and on which interface.
Logging can be toggled off an on by adjusting the `log` variable which
can be `true` or `false`.

CLI output from all commands is written to a file in the `logs/` directory.
A subdirectory for every execution of the playbook is created using
the format `nots_<date/time>/` which contains all the individual log files.`
The date/time uses ISO8601 short format, such as `20180522T134558`. Log files
are not version controlled and are excluded from git automatically. An example
log directory after three playbook runs against an inventory of two hosts
(csr1 and csr2), would yield something like this:

```
$ tree logs/
logs
├── nots_20180522T192916
│   ├── csr1.txt
│   └── csr2.txt
├── nots_20180522T194610
│   ├── csr1.txt
│   └── csr2.txt
└── nots_20180522T197133
    ├── csr1.txt
    └── csr2.txt
```

The contents of each log file begin with heading and trailing comment blocks
to show the command issued with its output. These logs are useful for finding
out why the playbook failed without having to manually log into failing hosts.
The example below shows the beginning of an IOS-based platform log file with
many redactions for brevity:

```
$ cat logs/nots_20180522T194610/csr1.txt
!!!
!!! Start command: show ip ospf 1
!!!
Routing Process "ospf 1" with ID 10.0.0.1
 Start time: 00:02:24.532, Time elapsed: 00:48:30.920
 Supports only single TOS(TOS0) routes
[snip, more output]
!!!
!!! End command:   show ip ospf 1
!!!
!!!
!!! Start command: show ip ospf 1 neighbor
!!!
Neighbor ID     Pri   State           Dead Time   Address         Interface
10.0.0.2          1   FULL/DR         00:00:39    192.168.102.2   Tunnel102
10.0.0.2          0   FULL/  -        00:00:37    192.168.101.2   Tunnel101
!!!
!!! End command:   show ip ospf 1 neighbor
!!!
[snip, more commands]
```

## FAQ
__Q__: Most code across IOS, IOS-XR, and NX-OS is the same. Why not combine it?\
__A__: The goal is to support more platforms in the future such as Cisco
ASA-OS, and possibly non-Cisco devices. These devices will likely return
different sets of information. This tool is designed to be __simple__,
not particularly advanced through layered abstractions.

__Q__: Why not use an API like RESTCONF or NETCONF instead of SSH + CLI?\
__A__: This tool is designed for risk-averse users or managers that are not
rapidly migrating to API-based management. It is not an infrastructure-as-code
solution and does not manage device configurations. All of the commands used
in the playbook can be issued at privilege level 1 to further reduce risk.
With the exception of updating the login credentials and populating the
necessary variables, there is no complex setup work required.

__Q__: Why not parse the OSPF interfaces? Many errors occur at this level.\
__A__: Parsing individual interfaces would require state declarations on a
per-host basis to determine what each interface __should__ have. This defeats
the purpose of a simple, low-effort solution which uses only area and process
level parameters for verification. Furthermore, the detailed statistics
checking will alert the user to many errors (authentication, MTU mismatch, etc)
at a more general level. The user can check the logs to see the exact commands,
which includes the non-parsed interface text.

__Q__: For NX-OS why didn't you use the `| json` filter from the CLI?\
__A__: While this would have saved a lot of parsing code, I did not want to
have an inconsistent overall strategy for one network device. Additionally,
the filter does not render milliseconds properly (eg, SPF throttle timers)
which reduced my confidence in its overall accuracy.
