# Cisco IOS/IOS-XE specifics

  * [Test cases](#summarized-test-cases)
  * [Group variables](#group-variables)

## Summarized test cases
The following test cases apply only to Cisco IOS and IOS-XE devices.

  * Sanity check: Ensure process ID matches what was specified.
    If this test fails, it is not indicative of a fault in your OSPF network,
    but rather is a logic error in the playbook code. Please submit an issue.
  * Ensure OSPF packet counters are below the error thresholds. The fields
    in scope for this test are enumerated below:
    * `adj_throttle`: Number of packets throttled due to adjacency limits.
    * `area_mismatch`: Number of packets received with mismatched area IDs.
    * `auth`: Number of packets with failed authentication keys.
    * `auth_type`: Number of packets with incorrect authentication type.
    * `bad_src`: Number of invalid source address or mismatched IP unnumbered.
    * `bfd`: Number of BFD related error packets relating to OSPF as a client.
    * `checksum`: Number of packets received with checksum failures.
    * `dup_rid`: Number of packets received with duplicate router IDs.
    * `hello_pkt`: Number of hello packet errors for various reasons.
    * `instance_id`: Number of mismatched instance IDs (RFC 6549).
    * `length`: Number of packets received with an invalid length.
    * `lls`: Number of link-local signaling errors (RFC 4813).
    * `lsa_checksum`: Number of LSAs received with invalid checksums.
    * `lsa_data`: Number of LSAs received with invalid payloads.
    * `lsa_length`: Number of LSAs received with an invalid length.
    * `lsa_type`: Number of LSAs received with an invalid type.
    * `mtu_mismatch`: Number of packets with MTU mismatches.
    * `nbr_ignored`: Number of packets received from an ignored neighbor.
    * `no_sl`: Number of packets received for a non-existent sham link.
    * `no_vl`: Number of packets received for a non-existent virtual link.
    * `self_orig`: It is not clear what this is measuring.
    * `test_discard`: It is not clear what this is measuring.
    * `ttlsec_fail`: Number of packets not meeting the TTL-security hop count.
    * `unk_nbr`: Number of packets received from an unknown neighbor.
    * `version`: Number of packets received from a non-OSPFv2 peer.
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
  * Ensure summary ASBR LSA (LSA type-4) count is 0 for NSSA and stub areas.
  * Ensure NSSA-external LSA (LSA type-7) count is less than threshold per NSSA.
  * Ensure LSA7 count is 0 for all non-NSSA areas.
  * Ensure external LSA (LSA type-5) count is less than threshold process wide.
  * Ensure Fast Re-Route (FRR) is enabled for the area (or not).

## Group variables
These subkeys are nested with a `process` dictionary which defines
process-wide parameters for a given OSPF process.

  * `id`: The process ID to check, an integer between 1 and 65535, inclusive.
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
