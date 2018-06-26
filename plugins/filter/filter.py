#!/usr/bin/python
'''
Author: Nick Russo <njrusmc@gmail.com>

File contains custom filters for use in Ansible playbooks.
https://www.ansible.com/
'''

from __future__ import print_function
import re
import ipaddress

class FilterModule(object):
    '''
    Defines a filter module object.
    '''

    @staticmethod
    def filters():
        '''
        Return a list of hashes where the key is the filter
        name exposed to playbooks and the value is the function.
        '''
        return {
            'ios_ospf_neighbor': FilterModule.ios_ospf_neighbor,
            'ios_ospf_basic': FilterModule.ios_ospf_basic,
            'ios_ospf_dbsum': FilterModule.ios_ospf_dbsum,
            'ios_ospf_traffic': FilterModule.ios_ospf_traffic,
            'ios_ospf_frr': FilterModule.ios_ospf_frr,
            'ios_bfd_neighbor': FilterModule.ios_bfd_neighbor,
            'check_bfd_up': FilterModule.check_bfd_up,
            'iosxr_ospf_traffic': FilterModule.iosxr_ospf_traffic,
            'iosxr_ospf_basic': FilterModule.iosxr_ospf_basic,
            'iosxr_ospf_neighbor': FilterModule.iosxr_ospf_neighbor,
            'nxos_ospf_basic': FilterModule.nxos_ospf_basic,
            'nxos_ospf_neighbor': FilterModule.nxos_ospf_neighbor,
            'nxos_ospf_dbsum': FilterModule.nxos_ospf_dbsum,
            'nxos_ospf_traffic': FilterModule.nxos_ospf_traffic
        }

    @staticmethod
    def _read_match(match, key_filler_list=None):
        '''
        Helper function which consumes a match object and an optional
        list of keys to populate with None values if match is invalid.
        Many operations follow this basic workflow, which iterates over
        the items captured in the match, attempts to make them integers
        whenever possible, and returns the resulting dict.
        '''
        return_dict = None
        if match:
            return_dict = match.groupdict()
            for key in return_dict.keys():
                return_dict[key] = FilterModule._try_int(return_dict[key])
        elif key_filler_list:
            return_dict = {}
            for key in key_filler_list:
                return_dict.update({key, None})

        return return_dict

    @staticmethod
    def _get_match_items(pattern, text, extra_flags=0):
        '''
        Helper function that can perform iterative block matching
        given a pattern and input text. Additional regex flags (re.DOTALL, etc)
        can be optionally specified. Any fields that can be parsed as
        integers are converted and the list of dictionaries containing the
        matches of each block is returned.
        '''
        regex = re.compile(pattern, re.VERBOSE + extra_flags)
        items = [match.groupdict() for match in regex.finditer(text)]
        for item in items:
            for key in item.keys():
                item[key] = FilterModule._try_int(item[key])

        return items

    @staticmethod
    def nxos_ospf_traffic(text):
        '''
        Parses information from the Cisco NXOS "show ip ospf traffic" command
        family. This is useful for verifying various characteristics of
        an OSPF process/area statistics for troubleshooting.
        '''

        process_pattern = r"""
            OSPF\s+Process\s+ID\s+(?P<pid>\d+)\s+
            .*?
            Ignored\s+LSAs:\s+(?P<ignore_lsa>\d+),\s+
            LSAs\s+dropped\s+during\s+SPF:\s+(?P<lsa_drop_spf>\d+)\s+
            LSAs\s+dropped\s+during\s+graceful\s+restart:\s+(?P<lsa_drop_gr>\d+)
            \s+Errors:\s+
            drops\s+in\s+(?P<drops_in>\d+),\s+
            drops\s+out\s+(?P<drops_out>\d+),\s+
            errors\s+in\s+(?P<errors_in>\d+),\s+
            errors\s+out\s+(?P<errors_out>\d+),\s+
            hellos\s+in\s+(?P<hellos_in>\d+),\s+
            dbds\s+in\s+(?P<dbds_in>\d+),\s+
            lsreq\s+in\s+(?P<lsreq_in>\d+),\s+
            lsu\s+in\s+(?P<lsu_in>\d+),\s+
            lsacks\s+in\s+(?P<lsacks_in>\d+),\s+
            unknown\s+in\s+(?P<unk_in>\d+),\s+
            unknown\s+out\s+(?P<unk_out>\d+),\s+
            no\s+ospf\s+(?P<no_ospf>\d+),\s+
            bad\s+version\s+(?P<bad_ver>\d+),\s+
            bad\s+crc\s+(?P<bad_crc>\d+),\s+
            dup\s+rid\s+(?P<dup_rid>\d+),\s+
            dup\s+src\s+(?P<dup_src>\d+),\s+
            invalid\s+src\s+(?P<inv_src>\d+),\s+
            invalid\s+dst\s+(?P<inv_dst>\d+),\s+
            no\s+nbr\s+(?P<no_nbr>\d+),\s+
            passive\s+(?P<passive>\d+),\s+
            wrong\s+area\s+(?P<wrong_area>\d+),\s+
            pkt\s+length\s+(?P<pkt_len>\d+),\s+
            nbr\s+changed\s+rid/ip\s+addr\s+(?P<nbr_change>\d+)\s+
            bad\s+auth\s+(?P<bad_auth>\d+),\s+
            no\s+vrf\s+(?P<no_vrf>\d+)
        """

        return FilterModule._get_match_items(process_pattern, text, re.DOTALL)

    @staticmethod
    def nxos_ospf_dbsum(text):
        '''
        Parses information from the Cisco NXOS
        "show ip ospf database database-summary" command family.
        This is useful for verifying various characteristics of
        an OSPF database to count LSAs for simple verification.
        '''
        return_dict = {}
        process_pattern = r"""
            Process\s+(?P<process_id>\d+)\s+database\s+summary\s+
            LSA\s+Type\s+Count\s+
            Opaque\s+Link\s+\d+\s+
            Router\s+(?P<total_lsa1>\d+)\s+
            Network\s+(?P<total_lsa2>\d+)\s+
            Summary\s+Network\s+(?P<total_lsa3>\d+)\s+
            Summary\s+ASBR\s+(?P<total_lsa4>\d+)\s+
            Type-7\s+AS\s+External\s+(?P<total_lsa7>\d+)\s+
            Opaque\s+Area\s+\d+\s+
            Type-5\s+AS\s+External\s+(?P<total_lsa5>\d+)
        """
        regex = re.compile(process_pattern, re.VERBOSE)
        match = regex.search(text)
        key_filler_list = [
            'process_id', 'total_lsa1', 'total_lsa2', 'total_lsa3',
            'total_lsa4', 'total_lsa5', 'total_lsa7'
        ]
        process = FilterModule._read_match(match, key_filler_list)

        return_dict.update({'process': process})

        area_pattern = r"""
            Area\s+(?P<id>\d+\.\d+\.\d+\.\d+)\s+database\s+summary\s+
            LSA\s+Type\s+Count\s+
            Opaque\s+Link\s+\d+\s+
            Router\s+(?P<num_lsa1>\d+)\s+
            Network\s+(?P<num_lsa2>\d+)\s+
            Summary\s+Network\s+(?P<num_lsa3>\d+)\s+
            Summary\s+ASBR\s+(?P<num_lsa4>\d+)\s+
            Type-7\s+AS\s+External\s+(?P<num_lsa7>\d+)\s+
        """

        areas = FilterModule._get_match_items(area_pattern, text)

        return_dict.update({'areas': areas})
        return return_dict

    @staticmethod
    def nxos_ospf_neighbor(text):
        '''
        Parses information from the Cisco NXOS "show ip ospf neighbor" command
        family. This is useful for verifying various characteristics of
        an OSPF neighbor's state.
        '''
        pattern = r"""
            (?P<rid>\d+\.\d+\.\d+\.\d+)\s+
            (?P<priority>\d+)\s+
            (?P<state>\w+)/\s*
            (?P<role>[A-Z-]+)\s+
            (?P<uptime>[0-9:]+)\s+
            (?P<peer>\d+\.\d+\.\d+\.\d+)\s+
            (?P<intf>[0-9A-Za-z./-]+)
        """
        return FilterModule._ospf_neighbor(pattern, text, ['uptime'])

    @staticmethod
    def nxos_ospf_basic(text):
        '''
        Parses information from the Cisco NXOS "show ospf" command
        family. This is useful for verifying various characteristics of
        an OSPF process and its basic configuration.
        '''
        return_dict = {}

        process_pattern = r"""
            Routing\s+Process\s+(?P<id>\d+)\s+with\s+ID\s+(?P<rid>\d+\.\d+\.\d+\.\d+)
            .*
            \s*Reference\s+Bandwidth\s+is\s+(?P<ref_bw>\d+)\s+Mbps
            .*
            \s*SPF\s+throttling\s+delay\s+time\s+of\s+(?P<init_spf>\d+)(?:\.\d+)\s+msecs,
            \s*SPF\s+throttling\s+hold\s+time\s+of\s+(?P<min_spf>\d+)(?:\.\d+)\s+msecs,
            \s*SPF\s+throttling\s+maximum\s+wait\s+time\s+of\s+(?P<max_spf>\d+)(?:\.\d+)\s+msecs
        """
        regex = re.compile(process_pattern, re.VERBOSE + re.DOTALL)
        match = regex.search(text)
        process = FilterModule._read_match(match, ['process'])
        if process:
            is_abr = text.find('area border') != -1
            is_asbr = text.find('autonomous system boundary') != -1
            is_stub_rtr = text.find('Originating router LSA with max') != -1

            process.update({
                'is_abr': is_abr,
                'is_asbr': is_asbr,
                'is_stub_rtr': is_stub_rtr
            })
            return_dict.update({'process': process})

        area_pattern = r"""
            Area\s+(?:BACKBONE)?\((?P<id_dd>\d+\.\d+\.\d+\.\d+)\)\s+
            \s+(?:Area\s+has\s+existed.*)\n
            \s+Interfaces\s+in\s+this\s+area:\s+(?P<num_intfs>\d+).*\n
            \s+(?:Passive.*)\n
            \s+(?:This\s+area\s+is\s+a\s+(?P<type>\w+)\s+area)?
        """

        regex = re.compile(area_pattern, re.VERBOSE)
        areas = [match.groupdict() for match in regex.finditer(text)]
        for area in areas:
            area['num_intfs'] = FilterModule._try_int(area['num_intfs'])
            converted_dd = ipaddress.IPv4Address(area['id_dd'])
            area['id'] = FilterModule._try_int(converted_dd)
            if not area['type']:
                area['type'] = 'standard'
            else:
                area['type'] = area['type'].lower()

        return_dict.update({'areas': areas})
        return return_dict

    @staticmethod
    def _try_int(text):
        '''
        Attempts to parse an integer from the input text. If it fails, just
        return the text as it was passed in. This is useful for iterating
        across structures with many integers which should be stored as
        integers, not strings.
        '''
        try:
            return int(text)
        except ValueError:
            return text

    @staticmethod
    def ios_ospf_neighbor(text):
        '''
        Parses information from the Cisco IOS "show ip ospf neighbor" command
        family. This is useful for verifying various characteristics of
        an OSPF neighbor's state.
        '''
        pattern = r"""
            (?P<rid>\d+\.\d+\.\d+\.\d+)\s+
            (?P<priority>\d+)\s+
            (?P<state>\w+)/\s*
            (?P<role>[A-Z-]+)\s+
            (?P<deadtime>[0-9:]+)\s+
            (?P<peer>\d+\.\d+\.\d+\.\d+)\s+
            (?P<intf>[0-9A-Za-z./-]+)
        """
        return FilterModule._ospf_neighbor(pattern, text, ['deadtime'])

    @staticmethod
    def ios_ospf_basic(text):
        '''
        Parses information from the Cisco IOS "show ospf" command
        family. This is useful for verifying various characteristics of
        an OSPF process and its basic configuration.
        '''
        return_dict = {}

        process_pattern = r"""
            Routing\s+Process\s+"ospf\s+(?P<id>\d+)"\s+with\s+ID\s+(?P<rid>\d+\.\d+\.\d+\.\d+)
            .*
            \s*Initial\s+SPF\s+schedule\s+delay\s+(?P<init_spf>\d+)\s+msecs
            \s*Minimum\s+hold\s+time\s+between\s+two\s+consecutive\s+SPFs\s+(?P<min_spf>\d+)\s+msecs
            \s*Maximum\s+wait\s+time\s+between\s+two\s+consecutive\s+SPFs\s+(?P<max_spf>\d+)\s+msecs
            .*
            \s*Reference\s+bandwidth\s+unit\s+is\s+(?P<ref_bw>\d+)\s+mbps
        """
        regex = re.compile(process_pattern, re.VERBOSE + re.DOTALL)
        match = regex.search(text)
        process = FilterModule._read_match(match, ['process'])
        if process:
            is_abr = text.find('area border') != -1
            is_asbr = text.find('autonomous system boundary') != -1
            is_stub_rtr = text.find('Originating router-LSAs with max') != -1
            has_ispf = text.find('Incremental-SPF enabled') != -1
            has_bfd = text.find('BFD is enabled') != -1
            has_ttlsec = text.find('Strict TTL checking enabled') != -1

            process.update({
                'is_abr': is_abr,
                'is_asbr': is_asbr,
                'is_stub_rtr': is_stub_rtr,
                'has_ispf': has_ispf,
                'has_bfd': has_bfd,
                'has_ttlsec': has_ttlsec
            })
            return_dict.update({'process': process})

        area_pattern = r"""
            Area\s+(?:BACKBONE\()?(?P<id>\d+)(?:\))?\s+
            Number\s+of\s+interfaces\s+in\s+this\s+area\s+is\s+(?P<num_intfs>\d+).*\n
            \s+(?:It\s+is\s+a\s+(?P<type>\w+)\s+area)?
        """

        regex = re.compile(area_pattern, re.VERBOSE)
        areas = [match.groupdict() for match in regex.finditer(text)]
        for area in areas:
            area['num_intfs'] = FilterModule._try_int(area['num_intfs'])
            area['id'] = FilterModule._try_int(area['id'])
            if not area['type']:
                area['type'] = 'standard'
            else:
                area['type'] = area['type'].lower()

        return_dict.update({'areas': areas})
        return return_dict

    @staticmethod
    def ios_ospf_dbsum(text):
        '''
        Parses information from the Cisco IOS
        "show ip ospf database database-summary" command family.
        This is useful for verifying various characteristics of
        an OSPF database to count LSAs for simple verification.
        Note that this parser is generic enough to cover Cisco IOS-XR also.
        '''
        return_dict = {}
        process_pattern = r"""
            Process\s+(?P<process_id>\d+)\s+database\s+summary\s+
            (?:LSA\s+Type\s+Count\s+Delete\s+Maxage\s+)?
            Router\s+(?P<total_lsa1>\d+).*\n\s+
            Network\s+(?P<total_lsa2>\d+).*\n\s+
            Summary\s+Net\s+(?P<total_lsa3>\d+).*\n\s+
            Summary\s+ASBR\s+(?P<total_lsa4>\d+).*\n\s+
            Type-7\s+Ext\s+(?P<total_lsa7>\d+).*
            \s+Type-5\s+Ext\s+(?P<total_lsa5>\d+)
        """
        regex = re.compile(process_pattern, re.VERBOSE + re.DOTALL)
        match = regex.search(text)
        key_filler_list = [
            'process_id', 'total_lsa1', 'total_lsa2', 'total_lsa3',
            'total_lsa4', 'total_lsa5', 'total_lsa7'
        ]
        process = FilterModule._read_match(match, key_filler_list)
        return_dict.update({'process': process})

        area_pattern = r"""
            Area\s+(?P<id>\d+)\s+database\s+summary\s+
            (?:LSA\s+Type\s+Count\s+Delete\s+Maxage\s+)?
            Router\s+(?P<num_lsa1>\d+).*\n\s+
            Network\s+(?P<num_lsa2>\d+).*\n\s+
            Summary\s+Net\s+(?P<num_lsa3>\d+).*\n\s+
            Summary\s+ASBR\s+(?P<num_lsa4>\d+).*\n\s+
            Type-7\s+Ext\s+(?P<num_lsa7>\d+)
        """

        areas = FilterModule._get_match_items(area_pattern, text)

        return_dict.update({'areas': areas})
        return return_dict

    @staticmethod
    def ios_ospf_traffic(text):
        '''
        Parses information from the Cisco IOS "show ip ospf traffic" command
        family. This is useful for verifying various characteristics of
        an OSPF process/area statistics for troubleshooting.
        '''

        interface_pattern = r"""
            Interface\s+(?P<intf>[^s]\S+)\s+
            .*?
            OSPF\s+header\s+errors
            \s+Length\s+(?P<length>\d+),
            \s+Instance\s+ID\s+(?P<instance_id>\d+),
            \s+Checksum\s+(?P<checksum>\d+),
            \s+Auth\s+Type\s+(?P<auth_type>\d+),
            \s+Version\s+(?P<version>\d+),
            \s+Bad\s+Source\s+(?P<bad_src>\d+),
            \s+No\s+Virtual\s+Link\s+(?P<no_vl>\d+),
            \s+Area\s+Mismatch\s+(?P<area_mismatch>\d+),
            \s+No\s+Sham\s+Link\s+(?P<no_sl>\d+),
            \s+Self\s+Originated\s+(?P<self_orig>\d+),
            \s+Duplicate\s+ID\s+(?P<dup_rid>\d+),
            \s+Hello\s+(?P<hello_pkt>\d+),
            \s+MTU\s+Mismatch\s+(?P<mtu_mismatch>\d+),
            \s+Nbr\s+Ignored\s+(?P<nbr_ignored>\d+),
            \s+LLS\s+(?P<lls>\d+),
            \s+Unknown\s+Neighbor\s+(?P<unk_nbr>\d+),
            \s+Authentication\s+(?P<auth>\d+),
            \s+TTL\s+Check\s+Fail\s+(?P<ttlsec_fail>\d+),
            \s+Adjacency\s+Throttle\s+(?P<adj_throttle>\d+),
            \s+BFD\s+(?P<bfd>\d+),
            \s+Test\s+discard\s+(?P<test_discard>\d+)
            \s*OSPF\s+LSA\s+errors
            \s+Type\s+(?P<lsa_type>\d+),
            \s+Length\s+(?P<lsa_length>\d+),
            \s+Data\s+(?P<lsa_data>\d+),
            \s+Checksum\s+(?P<lsa_checksum>\d+)
        """

        return FilterModule._get_match_items(interface_pattern, text, re.DOTALL)

    @staticmethod
    def ios_ospf_frr(text):
        '''
        Parses information from the Cisco IOS "show ip ospf fast-reroute"
        command family. This is useful for verifying various characteristics of
        OSPF FRR/LFA configuration to ensure it is configured correctly.
        '''

        pattern = r"""
            (?P<id>\d+)\s+
            (?P<topology>\w+)\s+
            (?P<pref_pri>(High|Low))\s+
            (?P<rlfa>(Yes|No))\s+
            (?P<tilfa>(Yes|No))
        """
        regex = re.compile(pattern, re.VERBOSE)
        frr_area_dict = {}
        for line in text.split('\n'):
            match = regex.search(line)
            if match:
                gdict = match.groupdict()
                area = 'area' + gdict['id']
                gdict['id'] = FilterModule._try_int(gdict['id'])
                gdict['rlfa'] = gdict['rlfa'].lower() == 'yes'
                gdict['tilfa'] = gdict['tilfa'].lower() == 'yes'
                gdict['pref_pri'] = gdict['pref_pri'].lower()
                gdict['topology'] = gdict['topology'].lower()

                frr_area_dict.update({area: gdict})

        return frr_area_dict

    @staticmethod
    def ios_bfd_neighbor(text):
        '''
        Parses information from the Cisco IOS "show bfd neighbor" command
        family. This is useful for verifying various characteristics of
        an BFD neighbor's state.
        '''

        pattern = r"""
            (?P<peer>\d+\.\d+\.\d+\.\d+)\s+
            (?P<ld>\d+)/
            (?P<rd>\d+)\s+
            (?P<rhrs>\w+)\s+
            (?P<state>\w+)\s+
            (?P<intf>[0-9A-Za-z./-]+)
        """
        regex = re.compile(pattern, re.VERBOSE)
        bfd_neighbors = []
        for line in text.split('\n'):
            match = regex.search(line)
            if match:
                gdict = match.groupdict()
                gdict['ld'] = FilterModule._try_int(gdict['ld'])
                gdict['rd'] = FilterModule._try_int(gdict['rd'])
                gdict['rhrs'] = gdict['rhrs'].lower()
                gdict['state'] = gdict['state'].lower()
                gdict['intf'] = gdict['intf'].lower()

                bfd_neighbors.append(gdict)

        return bfd_neighbors

    @staticmethod
    def check_bfd_up(bfd_nbr_list, ospf_nbr):
        '''
        Used to check if a specific OSPF neighbor (dictionary returned from
        ios_ospf_neighbor function) is present in the BFD neighbor list. This
        compares the OSPF neighbor interface IP, not router ID, against the
        BFD peer IP. It uses a simple linear search as the number of OSPF/BFD
        neighbors on a device tends to be small (few hundred).
        '''

        for bfd_nbr in bfd_nbr_list:
            if ospf_nbr['peer'] == bfd_nbr['peer']:
                is_up = bfd_nbr['state'] == 'up' and bfd_nbr['rhrs'] == 'up'
                return is_up

        raise ValueError('{0} not in bfd_nbr_list'.format(ospf_nbr['peer']))

    @staticmethod
    def iosxr_ospf_neighbor(text):
        '''
        Parses information from the Cisco IOS-XR "show ospf neighbor" command
        family. This is useful for verifying various characteristics of
        an OSPF neighbor's state.
        '''
        pattern = r"""
            (?P<rid>\d+\.\d+\.\d+\.\d+)\s+
            (?P<priority>\d+)\s+
            (?P<state>\w+)/\s*
            (?P<role>[A-Z-]+)\s+
            (?P<deadtime>[0-9:]+)\s+
            (?P<peer>\d+\.\d+\.\d+\.\d+)\s+
            (?P<uptime>[0-9:]+)\s+
            (?P<intf>[0-9A-Za-z./-]+)
        """
        return FilterModule._ospf_neighbor(
            pattern, text, ['deadtime', 'uptime'])

    @staticmethod
    def _ospf_neighbor(pattern, text, time_keys=None):
        '''
        Helper function specific to OSPF neighbor parsing. Each device type
        is slightly different in terms of the information provided, but
        most fields are the same. The time_keys parameter is a list of keys
        which are expected to have values in the format "hh:mm:ss". These
        are commonly uptime, deadtime, etc ... and are most useful when
        converted into seconds as an integer for comparative purposes.
        '''
        regex = re.compile(pattern, re.VERBOSE)
        ospf_neighbors = []
        for line in text.split('\n'):
            match = regex.search(line)
            if match:
                gdict = match.groupdict()
                gdict['priority'] = FilterModule._try_int(gdict['priority'])
                gdict['state'] = gdict['state'].lower()
                gdict['role'] = gdict['role'].lower()
                gdict['intf'] = gdict['intf'].lower()

                # If time keys is specified, iterate over the keys and perform
                # the math to convert hh:mm:ss to an integer of summed seconds.
                if time_keys:
                    for k in time_keys:
                        times = gdict[k].split(':')
                        parts = [FilterModule._try_int(t) for t in times]
                        totalsec = parts[0] * 3600 + parts[1] * 60 + parts[2]
                        gdict.update({k + '_sec': totalsec})

                ospf_neighbors.append(gdict)

        return ospf_neighbors

    @staticmethod
    def iosxr_ospf_basic(text):
        '''
        Parses information from the Cisco IOS-XR "show ospf" command
        family. This is useful for verifying various characteristics of
        an OSPF process and its basic configuration.
        '''
        return_dict = {}

        process_pattern = r"""
            Routing\s+Process\s+"ospf\s+(?P<id>\d+)"\s+with\s+ID\s+
            (?P<rid>\d+\.\d+\.\d+\.\d+)
            .*
            \s*Initial\s+SPF\s+schedule\s+delay\s+(?P<init_spf>\d+)\s+msecs
            \s*Minimum\s+hold\s+time\s+between\s+two\s+consecutive
            \s+SPFs\s+(?P<min_spf>\d+)\s+msecs
            \s*Maximum\s+wait\s+time\s+between\s+two\s+consecutive
            \s+SPFs\s+(?P<max_spf>\d+)\s+msecs
        """
        regex = re.compile(process_pattern, re.VERBOSE + re.DOTALL)
        match = regex.search(text)
        process = FilterModule._read_match(match, ['process'])
        if process:
            is_abr = text.find('area border') != -1
            is_asbr = text.find('autonomous system boundary') != -1
            is_stub_rtr = text.find('Originating router-LSAs with max') != -1

            process.update({
                'is_abr': is_abr,
                'is_asbr': is_asbr,
                'is_stub_rtr': is_stub_rtr,
            })
            return_dict.update({'process': process})

        area_pattern = r"""
            Area\s+(?:BACKBONE\()?(?P<id>\d+)(?:\))?\s+
            Number\s+of\s+interfaces\s+in\s+this\s+area\s+is\s+(?P<num_intfs>\d+).*?\n
            \s+(?:It\s+is\s+a\s+(?P<type>\w+)\s+area)?
            .*?
            Number\s+of\s+LFA\s+enabled\s+interfaces\s+(?P<frr_intfs>\d+)
        """

        regex = re.compile(area_pattern, re.VERBOSE + re.DOTALL)
        areas = [match.groupdict() for match in regex.finditer(text)]
        for area in areas:
            area['num_intfs'] = FilterModule._try_int(area['num_intfs'])
            area['id'] = FilterModule._try_int(area['id'])
            area['frr_intfs'] = FilterModule._try_int(area['frr_intfs'])
            if not area['type']:
                area['type'] = 'standard'
            else:
                area['type'] = area['type'].lower()

        return_dict.update({'areas': areas})
        return return_dict

    @staticmethod
    def iosxr_ospf_traffic(text):
        '''
        Parses information from the Cisco IOS-XR "show ip ospf traffic" command
        family. This is useful for verifying various characteristics of
        an OSPF process/area statistics for troubleshooting.
        '''

        interface_pattern = r"""
            Interface\s+(?P<intf>\S+)\s+
            Process\s+ID\s+(?P<pid>\d+)\s+
            Area\s+(?P<area_id>\d+)\s+
            .*?
            OSPF\s+Header\s+Errors
            \s+Version\s+(?P<version>\d+)
            \s+LLS\s+(?P<lls>\d+)
            \s+Type\s+(?P<type>\d+)
            \s+Auth\s+RX\s+(?P<auth_rx>\d+)
            \s+Length\s+(?P<length>\d+)
            \s+Auth\s+TX\s+(?P<auth_tx>\d+)
            \s+Checksum\s+(?P<checksum>\d+)
            \s*OSPF\s+LSA\s+Errors
            \s+Type\s+(?P<lsa_type>\d+)
            \s+Checksum\s+(?P<lsa_checksum>\d+)
            \s+Length\s+(?P<lsa_length>\d+)
            \s+Data\s+(?P<lsa_data>\d+)
            \s*OSPF\s+Errors
            \s+Bad\s+Source\s+(?P<bad_src>\d+)
            \s+Area\s+Mismatch\s+(?P<area_mismatch>\d+)
            \s+No\s+Virtual\s+Link\s+(?P<no_vl>\d+)
            \s+Self\s+Originated\s+(?P<self_orig>\d+)
            \s+No\s+Sham\s+Link\s+(?P<no_sl>\d+)
            \s+Duplicate\s+ID\s+(?P<dup_rid>\d+)
            \s+Nbr\s+ignored\s+(?P<nbr_ignored>\d+)
            \s+Graceful\s+Shutdown\s+(?P<gshut>\d+)
            \s+Unknown\s+nbr\s+(?P<unk_nbr>\d+)
            \s+Passive\s+intf\s+(?P<passive_intf>\d+)
            \s+No\s+DR/BDR\s+(?P<no_dr_bdr>\d+)
            \s+Disabled\s+intf\s+(?P<disable_intf>\d+)
            \s+Enqueue\s+hello\s+(?P<enq_hello>\d+)
            \s+Enqueue\s+router\s+(?P<enq_rtr>\d+)
            \s+Unspecified\s+RX\s+(?P<unspec_rx>\d+)
            \s+Unspecified\s+TX\s+(?P<unspec_tx>\d+)
            \s+Socket\s+(?P<socket>\d+)
        """

        return FilterModule._get_match_items(interface_pattern, text, re.DOTALL)
