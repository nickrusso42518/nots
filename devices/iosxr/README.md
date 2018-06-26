# Cisco IOS-XR specifics

  * [Test cases](#summarized-test-cases)
  * [Group variables](#group-variables)

## Summarized test cases
The following test cases apply only to IOS-XR devices.

  * Sanity check: Ensure process ID matches what was specified.
    If this test fails, it is not indicative of a fault in your OSPF network,
    but rather is a logic error in the playbook code. Please submit an issue.
  * Ensure OSPF packet counters are below the error thresholds. The fields
    in scope for this test are enumerated below:
    * `version`: Number of packets received from a non-OSPFv2 peer.
    * `type`: Number of packets received of the incorrect type.
    * `length`: Number of packets received with an invalid length.
    * `checksum`: Number of packets received with checksum failures.
    * `lls`: Number of link-local signaling errors (RFC 4813).
    * `auth_rx`: Number of packets received with failed authentication.
    * `auth_tx`: Number of packets transmitted with failed authentication.
    * `lsa_type`: Number of LSAs received with an invalid type.
    * `lsa_length`: Number of LSAs received with an invalid length.
    * `lsa_checksum`: Number of LSAs received with invalid checksums.
    * `lsa_data`: Number of LSAs received with invalid payloads.
    * `bad_src`: Number of invalid source address or mismatched IP unnumbered.
    * `no_vl`: Number of packets received for a non-existent virtual link.
    * `no_sl`: Number of packets received for a non-existent sham link.
    * `nbr_ignored`: Number of packets received from an ignored neighbor.
    * `unk_nbr`: Number of packets received from an unknown neighbor.
    * `no_dr_bdr`: Numbers of packets on a broadcast network without a DR/BDR.
    * `enq_hello`: It is not clear what this is measuring.
    * `unspec_rx`: It is not clear what this is measuring.
    * `socket`: Number of packets dropped due to a socket error.
    * `area_mismatch`: Number of packets received with mismatched area IDs.
    * `self_orig`: LSAs received by router that were originated by this router.
    * `dup_rid`: Number of packets received with duplicate router IDs.
    * `gshut`: Number of graceful shutdown packets received.
    * `passive_intf`: Nubmer of packets received on a passive interface.
    * `disable_intf`: Nubmer of packets received on a disabled interface.
    * `enq_rtr`: It is not clear what this is measuring.
    * `unspec_tx`: It is not clear what this is measuring.
  * Ensure correct number of OSPF neighbors are seen.
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
  * Ensure Fast Re-Route (FRR) is enabled for the area (or not).

## Group variables
These subkeys are nested with a `process` dictionary which defines
process-wide parameters for a given OSPF process.

  * `id`: The process ID to check, an integer between 1 and 65535, inclusive.
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
