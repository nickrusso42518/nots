#!/usr/bin/python
'''
Author: Nick Russo <njrusmc@gmail.com>
Last modified: 23 March 2018

File contains custom filters for use in Ansible playbooks.
https://www.ansible.com/
'''

from __future__ import print_function
import string
import re
from StringIO import StringIO

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
            'iosxr_ospf_neighbor': FilterModule.iosxr_ospf_neighbor
        }

    @staticmethod
    def _try_int(text):
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
        regex = re.compile(pattern, re.VERBOSE)
        ospf_neighbors = []
        for s in text.split('\n'):
            m = regex.search(s)
            if m:
                d = m.groupdict()
                d['priority'] = FilterModule._try_int(d['priority'])

                dead_times = d['deadtime'].split(':')
                times = [FilterModule._try_int(t) for t in dead_times]
                deadsec = times[0] * 3600 + times[1] * 60 + times[2]
                d.update({'deadsec': deadsec})

                ospf_neighbors.append(d)

        return ospf_neighbors

# Routing Process "ospf 1" with ID 10.0.0.5
# It is an area border and autonomous system boundary router
# Reference bandwidth unit is 100 mbps
#    Area BACKBONE(0)
#        Number of interfaces in this area is 3 (1 loopback)
#    Area 4
#        Number of interfaces in this area is 1
#        It is a NSSA area

# Initial SPF schedule delay 5000 msecs
# Minimum hold time between two consecutive SPFs 10000 msecs
# Maximum wait time between two consecutive SPFs 10000 msecs
    @staticmethod
    def ios_ospf_basic(text):
        '''
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
        if match:
            process = match.groupdict()
            for key in process.keys():
                process[key] = FilterModule._try_int(process[key])

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
        else:
            return_dict.update({'process': None})
        
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

#
#            OSPF Router with ID (10.0.0.1) (Process ID 1)
#
#Area 0 database summary
#  LSA Type      Count    Delete   Maxage
#  Router        9        0        0
#  Network       1        0        0
#  Summary Net   54       0        0
#  Summary ASBR  4        0        0
#  Type-7 Ext    0        0        0
#    Prefixes redistributed in Type-7  0
#  Opaque Link   0        0        0
#  Opaque Area   0        0        0
#  Subtotal      68       0        0
#
#Area 3 database summary
#  LSA Type      Count    Delete   Maxage
#  Router        4        0        0
#  Network       0        0        0
#  Summary Net   64       0        0
#  Summary ASBR  6        0        0
#  Type-7 Ext    0        0        0
#    Prefixes redistributed in Type-7  0
#  Opaque Link   0        0        0
#  Opaque Area   0        0        0
#  Subtotal      74       0        0
#
#Process 1 database summary
#  LSA Type      Count    Delete   Maxage
#  Router        13       0        0
#  Network       1        0        0
#  Summary Net   118      0        0
#  Summary ASBR  10       0        0
#  Type-7 Ext    0        0        0
#  Opaque Link   0        0        0
#  Opaque Area   0        0        0
#  Type-5 Ext    1        0        0
#      Prefixes redistributed in Type-5  0
#  Opaque AS     0        0        0
#  Non-self      99
#  Total         143      0        0
    @staticmethod
    def ios_ospf_dbsum(text):
        '''
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
        if match:
            process = match.groupdict()
            for key in process.keys():
                process[key] = FilterModule._try_int(process[key])
        else:
            process = {
                'process_id': -1,
                'total_lsa1': -1,
                'total_lsa2': -1,
                'total_lsa3': -1,
                'total_lsa4': -1,
                'total_lsa5': -1,
                'total_lsa7': -1
            }
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

        regex = re.compile(area_pattern, re.VERBOSE)
        areas = [match.groupdict() for match in regex.finditer(text)]
        for area in areas:
            for key in area.keys():
                area[key] = FilterModule._try_int(area[key])

        return_dict.update({'areas': areas})
        return return_dict

    @staticmethod
    def ios_ospf_traffic(text):
        '''
        '''

        interface_pattern = r"""
            Interface\s+(?P<intf>\S+)\s+
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

        regex = re.compile(interface_pattern, re.VERBOSE + re.DOTALL)
        intfs = [match.groupdict() for match in regex.finditer(text)]
        for intf in intfs:
            for key in intf.keys():
                intf[key] = FilterModule._try_int(intf[key])

        return intfs

    @staticmethod
    def ios_ospf_frr(text):
        '''
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
        for s in text.split('\n'):
            m = regex.search(s)
            if m:
                d = m.groupdict()
                area = 'area' + d['id']
                d['id'] = FilterModule._try_int(d['id'])
                d['rlfa'] = d['rlfa'].lower() == 'yes'
                d['tilfa'] = d['tilfa'].lower() == 'yes'
                d['pref_pri'] = d['pref_pri'].lower()
                d['topology'] = d['topology'].lower()

                frr_area_dict.update({area: d})

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
        for s in text.split('\n'):
            m = regex.search(s)
            if m:
                d = m.groupdict()
                d['ld'] = FilterModule._try_int(d['ld'])
                d['rd'] = FilterModule._try_int(d['rd'])
                d['rhrs'] = d['rhrs'].lower()
                d['state'] = d['state'].lower()
                d['intf'] = d['intf'].lower()

                bfd_neighbors.append(d)

        return bfd_neighbors

    @staticmethod
    def check_bfd_up(bfd_nbr_list, ospf_nbr):
        '''
        '''

        for bfd_nbr in bfd_nbr_list:
            if ospf_nbr['peer'] == bfd_nbr['peer']:
                is_up = bfd_nbr['state'] == 'up' and bfd_nbr['rhrs'] == 'up'
                return is_up

        raise ValueError('Peer {0} not found in bfd_nbr_list'.format(ospf_nbr['peer']))
    

    @staticmethod
    def iosxr_ospf_neighbor(text):
        '''
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
        regex = re.compile(pattern, re.VERBOSE)
        ospf_neighbors = []
        for s in text.split('\n'):
            m = regex.search(s)
            if m:
                d = m.groupdict()
                d['priority'] = FilterModule._try_int(d['priority'])
                d['state'] = d['state'].lower()
                d['role'] = d['role'].lower()

                dead_times = d['deadtime'].split(':')
                times = [FilterModule._try_int(t) for t in dead_times]
                deadsec = times[0] * 3600 + times[1] * 60 + times[2]
                d.update({'deadsec': deadsec})

                up_times = d['uptime'].split(':')
                times = [FilterModule._try_int(t) for t in up_times]
                upsec = times[0] * 3600 + times[1] * 60 + times[2]
                d.update({'deadsec': upsec})

                ospf_neighbors.append(d)

        return ospf_neighbors

    @staticmethod
    def iosxr_ospf_basic(text):
        '''
        '''
        return_dict = {}

        process_pattern = r"""
            Routing\s+Process\s+"ospf\s+(?P<id>\d+)"\s+with\s+ID\s+(?P<rid>\d+\.\d+\.\d+\.\d+)
            .*
            \s*Initial\s+SPF\s+schedule\s+delay\s+(?P<init_spf>\d+)\s+msecs
            \s*Minimum\s+hold\s+time\s+between\s+two\s+consecutive\s+SPFs\s+(?P<min_spf>\d+)\s+msecs
            \s*Maximum\s+wait\s+time\s+between\s+two\s+consecutive\s+SPFs\s+(?P<max_spf>\d+)\s+msecs
        """
        regex = re.compile(process_pattern, re.VERBOSE + re.DOTALL)
        match = regex.search(text)
        if match:
            process = match.groupdict()
            for key in process.keys():
                process[key] = FilterModule._try_int(process[key])

            is_abr = text.find('area border') != -1
            is_asbr = text.find('autonomous system boundary') != -1
            is_stub_rtr = text.find('Originating router-LSAs with max') != -1

            process.update({
                'is_abr': is_abr,
                'is_asbr': is_asbr,
                'is_stub_rtr': is_stub_rtr,
            })
            return_dict.update({'process': process})
        else:
            return_dict.update({'process': None})

        area_pattern = r"""
            Area\s+(?:BACKBONE\()?(?P<id>\d+)(?:\))?\s+
            Number\s+of\s+interfaces\s+in\s+this\s+area\s+is\s+(?P<num_intfs>\d+).*?\n
            \s+(?:It\s+is\s+a\s+(?P<type>\w+)\s+area)?
            .*?
            Number\s+of\s+LFA\s+enabled\s+interfaces\s+(?P<lfa_intfs>\d+)
        """

        regex = re.compile(area_pattern, re.VERBOSE + re.DOTALL)
        areas = [match.groupdict() for match in regex.finditer(text)]
        for area in areas:
            area['num_intfs'] = FilterModule._try_int(area['num_intfs'])
            area['id'] = FilterModule._try_int(area['id'])
            area['lfa_intfs'] = FilterModule._try_int(area['lfa_intfs'])
            if not area['type']:
                area['type'] = 'standard'
            else:
                area['type'] = area['type'].lower()

        return_dict.update({'areas': areas})
        return return_dict

    @staticmethod
    def iosxr_ospf_traffic(text):
        '''
        '''

        interface_pattern = r"""
            Interface\s+(?P<intf>\S+)\s+
            Process\s+ID\s+(?P<pid>\d+)\s+
            Area\s+(?P<area_id>\d+)\s+
            .*?
            OSPF\s+Header\s+Errors
            \s+Version\s+(?P<version>\d+)
            \s+LLS\s+(?P<lls>\d+)
            \s+Type\s+(?P<hdr_type>\d+)
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
            \s+Disabled\s+intf\s+(?P<disabled_intf>\d+)
            \s+Enqueue\s+hello\s+(?P<enq_hello>\d+)
            \s+Enqueue\s+router\s+(?P<enq_rtr>\d+)
            \s+Unspecified\s+RX\s+(?P<unspec_rx>\d+)
            \s+Unspecified\s+TX\s+(?P<unspec_tx>\d+)
            \s+Socket\s+(?P<socket>\d+)
        """

        regex = re.compile(interface_pattern, re.VERBOSE + re.DOTALL)
        intfs = [match.groupdict() for match in regex.finditer(text)]
        for intf in intfs:
            for key in intf.keys():
                intf[key] = FilterModule._try_int(intf[key])

        return intfs

