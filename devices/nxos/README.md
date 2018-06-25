# Cisco Nexus OS (NXOS) Specifications

  * [Test cases](#summarized-test-cases)
  * [Group variables](#group-variables)

## Summarized test cases
The following test cases apply only to Cisco NXOS devices.

  * Sanity check: Ensure process ID matches what was specified.
    If this test fails, it is not indicative of a fault in your OSPF network,
    but rather is a logic error in the playbook code. Please submit an issue.
  * Ensure OSPF packet counters are below the error thresholds. The fields
    in scope for this test are enumerated below:
    * `bad_auth`: Packets received with invalid/mismatched authentication.
    * `bad_crc`: Bad CRC packets which are malformed (and discarded).
    * `bad_ver`: Packets received with the wrong OSPF version.
    * `dbds_in`: Malformed database descriptor messages received.
    * `drops_in`: Inbound packets that were dropped.
    * `drops_out`: Outbound packets that were dropped.
    * `dup_rid`: Number of packets received with duplicate router IDs.
    * `dup_src`: Number of duplicated source address packets received.
    * `error_in`: Packets received with errors.
    * `error_out`: Packets sent with errors.
    * `hello_in`: Malformed OSPF hello packets received.
    * `inv_crc`: Invalid CRC packets. Unclear how it differs from `bad_src`.
    * `inv_dest`: OSPF packets with invalid destination IP addresses.
    * `lsacks_in`: Malformed link state acknowledgements received.
    * `lsreq_in`: Malformed link state requests received.
    * `lsu_in`:  Malformed link state updates received.
    * `nbr_change`: Number of packets with RID/IP not matching expected values.
    * `no_nbr`: Number of packets from a router that is not a full neighbor.
    * `no_ospf`: Packets received on an interface without OSPF enabled?
    * `no_vrf`: Packets received in an OSPF process with a VRF issue?
    * `passive`: Packets received on a passive interface.
    * `pkt_len`: Packets received with an invalid length (too big/small).
    * `unk_in`: Unknown OSPF packets received.
    * `unk_out`: Unknown OSPF packets sent.
    * `wrong_area`: Packets received in the wrong area (area mismatch).
  * Ensure correct number of OSPF neighbors are seen.
  * Ensure correct configuration of auto-cost reference bandwidth.
  * Ensure correct configuration of SPF throttle timers.
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
  * Ensure summary ASBR LSA (LSA type-4) count is 0 for NSSA and stub areas.
  * Ensure NSSA-external LSA (LSA type-7) count is less than threshold per NSSA.
  * Ensure LSA7 count is 0 for all non-NSSA areas.
  * Ensure external LSA (LSA type-5) count is less than threshold process wide.

## Group variables
These subkeys are nested with a `process` dictionary which defines
process-wide parameters for a given OSPF process.

  * `id`: The process ID to check, an integer between 1 and 65535, inclusive.
  * `ref_bw`: The auto-cost reference-bandwidth specified. Note that even when
     an explicit value is not configured, many devices have a default value
     of 100 (implying a link with speed 100 Mbps has a cost of 1).
  * `max_lsa5`: The maximum number of external LSAs (LSA type-5) that should be
    present within the entire process. This inclusive upper bound enforces a
    limit on the number of LSA5 for the purpose of flood reduction and memory
    consumption. It can also enforce specific architectural designs. For
    example, ensuring that a large quantity of public Internet routes are not
    redistributed into OSPF at the Internet edge, but instead, only a default
    and some select longer matches are redistributed.
    To disable this check, exclude this key.
  * `spf`: Key containing an embedded dictionary with individual timers:
    * `init`: The SPF reaction time after the first failure (default 50).
    * `min`: The SPF reaction time after the next failure (default 200).
    * `max`: The longest possible SPF reaction time (default 5000).
