# Nick's OSPF TroubleShooter (nots)
A simple but powerful Ansible playbook to troubleshoot OSPF network problems
on a variety of platforms. It is simple because it does not require
extensive preparatory configuration for individual host state checking.
It is powerful because despite not having the aforementioned level of
granularity, it rapidly discovers the vast majority of OSPF problems.

## Supported platforms
Today, Cisco IOS/IOS-XE and IOS-XR are supported. The valid `device_type`
options used for inventory groups are enumerated below.

  * `ios`: Cisco classic IOS and Cisco IOS-XE devices.
  * `iosxr`: __FUTURE__ Cisco IOS-XR devices.
  * `nxos`: __FUTURE__ Cisco Nexus OS devices.
  * `asa`: __FUTURE__ Cisco ASA OS devices.

## Summarized test cases
The following tests are run in sequence. Note that the exact items tested
varies between platforms since command outputs and feature sets also vary.
Administrative tasks, such as creating directories and logging on the control
machine, are not detailed here for brevity.

### Per host testing
Ansible logs into each OSPF router for the purpose of collecting information
and validating its correctness based on a small amount of pre-identified
state configuration. As discussed in the "variables" section, some of these
tests can be skipped by modifying the appropriate key/value pairs.

  * Sanity check: Ensure process ID matches what was specified.
    If this test fails, it is not indicative of a fault in your OSPF network,
    but rather is a logic error in the playbook code. Please submit an issue.
  * Ensure OSPF packet counters are below the error thresholds.
  * Ensure correct number of OSPF neighbors are seen.
  * Ensure OSPF neighbors are also BFD neighbors (or not).
  * Ensure correct configuration of auto-cost reference bandwidth.
  * Ensure correct configuration of SPF throttle timers.
  * Ensure correct configuration of iSPF.
  * Ensure the process has BFD enabled globally (or not).
  * Ensure the process has TTL-security enabled globally (or not).
  * Ensure that routers in area 0 and at least one other area see themselves
    as Area Border Routers (ABR).
  * Ensure that routers identified by the user as Autonomous System Boundary
    Routers (ASBR) see themselves as such. This includes Not-So-Stubby-Area
    (NSSA) ABRs as they could originate external LSAs (LSA type-5).
  * Ensure the router has stub router (max-metric) enabled (or not).
  * Ensure the correct area type (standard, stub, or nssa) per area.
  * Ensure correct number of router LSAs (LSA type-1) per area.
  * Ensure correct number of network LSAs (LSA type-2) per area.
  * Ensure summary LSA (LSA type-3) count is less than threshold per area.
  * Ensure external LSA (LSA type-5) count is less than threshold per area.
  * Ensure NSSA-external LSA (LSA type-7) count is less than threshold per area.
  * Ensure Fast Re-Route (FRR) is enabled for the area (or not).

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

  * `id`: The process ID to check, an integer between 1 and 65535, inclusive.
  * `pkt_thres`: Inclusive upper bound measuring the number of packet, header,
     and LSA errors seen. The default threshold is 0, implying no
     errors are tolerated.
  * `has_ispf`: Boolean representing whether incremental SPF should be enabled
     (`true`) or disabled (`false`) for this process.
  * `has_ttlsec`: Boolean representing whether TTL security should be enabled
     (`true`) or disabled (`false`) for this process. This is technically an
     interface level configuration, but for simplicity, the playbook enforces
     "all of nothing" configuration for this feature.
     (`true`) or disabled (`false`) for this process.
  * `has_bfd`: Boolean representing whether Bidirectional Forwarding Detection
     should be enabled (`true`) or disabled (`false`) for this process.
     This is technically an interface level configuration, but for simplicity,
     the playbook enforces "all of nothing" configuration for this feature.
  * `ref_bw`: The auto-cost reference-bandwidth specified.
  * `init_spf`: The SPF reaction time after the first failure (default 50).
  * `min_spf`: The SPF reaction time after the next failure (default 200).
  * `max_spf`: The longest possible SPF reaction time (default 5000).

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
  * `max_lsa5`: The maximum number of external LSAs (LSA type-5) that should be
    present within an area. This inclusive upper bound enforces a limit on
    the number of LSA5 for the purpose of flood reduction and memory
    consumption. It can also enforce specific architectural designs. For
    example, ensuring that a large quantity of public Internet routes are not
    redistributed into OSPF at the Internet edge, but instead, only a default
    and some select longer matches are redistributed. This key is only
    processed when the area type is "standard".
    To disable this check, exclude this key.
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
contains OS-specific parameters. __These should be changed by consumers
as their main purpose is abstraction and not user input.__

  * `device_type`: A string representing the device OS name. These were
    enumerated in the "Supported Platforms" section earlier in the document.
  * `commands`: A list of strings representing the CLI commands to be
    issued to the device. These collect information from the devices relevant
    to troubleshooting OSPF.

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
to show the command issued with its output. Example below:

```
$ cat logs/nots_20180521T165814/csr1.txt
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
