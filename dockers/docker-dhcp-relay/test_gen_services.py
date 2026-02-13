VLAN = """
{
    "Vlan1000": {
        "admin_status": "up",
        "dhcp_relay_src_intf": "Vlan1000",
        "dhcp_servers": [
            "10.239.8.11",
            "10.239.8.12"
        ],
        "members": [
            "Ethernet120",
            "Ethernet124"
        ],
        "vlanid": "1000"
    },
    "Vlan1200": {
        "admin_status": "up",
        "dhcp_relay_src_intf": "Vlan1000",
        "dhcp_servers": [
            "10.239.8.11",
            "10.239.8.12"
        ],
        "members": [
            "Ethernet120",
            "Ethernet124"
        ],
        "vlanid": "1200"
    }
}"""

VLAN_INTERFACE="""{
    "Vlan1000": {},
    "Vlan1200": {},
    "Vlan1000|10.242.21.1/24": {},
    "Vlan1000|10.242.31.1/24": {
        "secondary": "true"
    },
    "Vlan1200|10.242.22.1/24": {}
}"""

INTERFACE = """{
    "Ethernet0": {},
    "Ethernet100": {},
    "Ethernet104": {},
    "Ethernet108": {},
    "Ethernet112": {},
    "Ethernet116": {},
    "Ethernet12": {},
    "Ethernet128": {},
    "Ethernet129": {},
    "Ethernet16": {},
    "Ethernet20": {},
    "Ethernet24": {},
    "Ethernet28": {},
    "Ethernet32": {},
    "Ethernet36": {},
    "Ethernet4": {},
    "Ethernet40": {},
    "Ethernet44": {},
    "Ethernet48": {},
    "Ethernet52": {},
    "Ethernet56": {},
    "Ethernet60": {},
    "Ethernet64": {},
    "Ethernet68": {},
    "Ethernet72": {},
    "Ethernet76": {},
    "Ethernet8": {},
    "Ethernet80": {},
    "Ethernet84": {},
    "Ethernet88": {},
    "Ethernet92": {},
    "Ethernet96": {},
    "Ethernet0|10.0.0.0/31": {},
    "Ethernet100|10.0.0.50/31": {},
    "Ethernet104|10.0.0.52/31": {},
    "Ethernet108|10.0.0.54/31": {},
    "Ethernet112|10.0.0.56/31": {},
    "Ethernet116|10.0.0.58/31": {},
    "Ethernet128|10.0.0.64/31": {},
    "Ethernet129|10.0.0.66/31": {},
    "Ethernet12|10.0.0.6/31": {},
    "Ethernet16|10.0.0.8/31": {},
    "Ethernet20|10.0.0.10/31": {},
    "Ethernet24|10.0.0.12/31": {},
    "Ethernet28|10.0.0.14/31": {},
    "Ethernet32|10.0.0.16/31": {},
    "Ethernet36|10.0.0.18/31": {},
    "Ethernet40|10.0.0.20/31": {},
    "Ethernet44|10.0.0.22/31": {},
    "Ethernet48|10.0.0.24/31": {},
    "Ethernet4|10.0.0.2/31": {},
    "Ethernet52|10.0.0.26/31": {},
    "Ethernet56|10.0.0.28/31": {},
    "Ethernet60|10.0.0.30/31": {},
    "Ethernet64|10.0.0.32/31": {},
    "Ethernet68|10.0.0.34/31": {},
    "Ethernet72|10.0.0.36/31": {},
    "Ethernet76|10.0.0.38/31": {},
    "Ethernet80|10.0.0.40/31": {},
    "Ethernet84|10.0.0.42/31": {},
    "Ethernet88|10.0.0.44/31": {},
    "Ethernet8|10.0.0.4/31": {},
    "Ethernet92|10.0.0.46/31": {},
    "Ethernet96|10.0.0.48/31": {}
}"""

DEVICE_METADATA = """{
    "localhost": {
        "bgp_asn": "65100",
        "buffer_model": "traditional",
        "default_bgp_status": "up",
        "default_pfcwd_status": "disable",
        "hostname": "sonic",
        "hwsku": "DellEMC-S5232f-C32",
        "mac": "20:88:10:58:f9:80",
        "platform": "x86_64-dellemc_s5232f_c3538-r0",
        "timezone": "UTC",
        "type": "LeafRouter"
    }
}"""
DHCP_RELAY="""
{
    "Vlan1000": {
        "dhcpv6_servers": [
            "fc00:1::1",
            "fc00:1::2"
        ]
    },
    "Vlan1200": {
        "dhcpv6_servers": [
            "fc00:1::1",
            "fc00:1::2"
        ]
    }
}"""
PORTCHANNEL_INTERFACE=""

import unittest
import json
import yaml
from typing import Dict, Any
from gen_services import gen_all_config, get_start_order

class TestGenPebbleConfig(unittest.TestCase):

    def setUp(self):
        self.vlan = json.loads(VLAN)
        self.vlan_interface = json.loads(VLAN_INTERFACE)
        self.interface = json.loads(INTERFACE)
        self.device_metadata = json.loads(DEVICE_METADATA)
        self.dhcp_relay = json.loads(DHCP_RELAY) if DHCP_RELAY else {}
        self.portchannel_interface = json.loads(PORTCHANNEL_INTERFACE) if PORTCHANNEL_INTERFACE else {}

    def test_gen_config(self):
        # Generate complete config
        yaml_output = gen_all_config(
            self.vlan,
            self.vlan_interface,
            self.interface,
            self.portchannel_interface,
            self.device_metadata,
            self.dhcp_relay)
        raw_str = yaml.dump(yaml_output, sort_keys=False, width=float("inf"))

        expected_yaml = """services:
  isc-dhcpv4-relay-Vlan1000:
    command: /usr/sbin/dhcrelay -d -m discard -a %h:%p %P --name-alias-map-file /tmp/port-name-alias-map.txt -id Vlan1000 -iu Vlan1200 -iu Ethernet0 -iu Ethernet100 -iu Ethernet104 -iu Ethernet108 -iu Ethernet112 -iu Ethernet116 -iu Ethernet128 -iu Ethernet129 -iu Ethernet12 -iu Ethernet16 -iu Ethernet20 -iu Ethernet24 -iu Ethernet28 -iu Ethernet32 -iu Ethernet36 -iu Ethernet40 -iu Ethernet44 -iu Ethernet48 -iu Ethernet4 -iu Ethernet52 -iu Ethernet56 -iu Ethernet60 -iu Ethernet64 -iu Ethernet68 -iu Ethernet72 -iu Ethernet76 -iu Ethernet80 -iu Ethernet84 -iu Ethernet88 -iu Ethernet8 -iu Ethernet92 -iu Ethernet96 -pg 10.242.21.1 10.239.8.11 10.239.8.12
    override: replace
  isc-dhcpv4-relay-Vlan1200:
    command: /usr/sbin/dhcrelay -d -m discard -a %h:%p %P --name-alias-map-file /tmp/port-name-alias-map.txt -id Vlan1200 -iu Vlan1000 -iu Vlan1000 -iu Ethernet0 -iu Ethernet100 -iu Ethernet104 -iu Ethernet108 -iu Ethernet112 -iu Ethernet116 -iu Ethernet128 -iu Ethernet129 -iu Ethernet12 -iu Ethernet16 -iu Ethernet20 -iu Ethernet24 -iu Ethernet28 -iu Ethernet32 -iu Ethernet36 -iu Ethernet40 -iu Ethernet44 -iu Ethernet48 -iu Ethernet4 -iu Ethernet52 -iu Ethernet56 -iu Ethernet60 -iu Ethernet64 -iu Ethernet68 -iu Ethernet72 -iu Ethernet76 -iu Ethernet80 -iu Ethernet84 -iu Ethernet88 -iu Ethernet8 -iu Ethernet92 -iu Ethernet96 10.239.8.11 10.239.8.12
    override: replace
  dhcp6relay:
    command: /usr/sbin/dhcp6relay
    override: replace
  dhcpmon-Vlan1000:
    command: /usr/sbin/dhcpmon -id Vlan1000 -iu Vlan1200 -iu Ethernet0 -iu Ethernet100 -iu Ethernet104 -iu Ethernet108 -iu Ethernet112 -iu Ethernet116 -iu Ethernet128 -iu Ethernet129 -iu Ethernet12 -iu Ethernet16 -iu Ethernet20 -iu Ethernet24 -iu Ethernet28 -iu Ethernet32 -iu Ethernet36 -iu Ethernet40 -iu Ethernet44 -iu Ethernet48 -iu Ethernet4 -iu Ethernet52 -iu Ethernet56 -iu Ethernet60 -iu Ethernet64 -iu Ethernet68 -iu Ethernet72 -iu Ethernet76 -iu Ethernet80 -iu Ethernet84 -iu Ethernet88 -iu Ethernet8 -iu Ethernet92 -iu Ethernet96
    override: replace
  dhcpmon-Vlan1200:
    command: /usr/sbin/dhcpmon -id Vlan1200 -iu Vlan1000 -iu Vlan1000 -iu Ethernet0 -iu Ethernet100 -iu Ethernet104 -iu Ethernet108 -iu Ethernet112 -iu Ethernet116 -iu Ethernet128 -iu Ethernet129 -iu Ethernet12 -iu Ethernet16 -iu Ethernet20 -iu Ethernet24 -iu Ethernet28 -iu Ethernet32 -iu Ethernet36 -iu Ethernet40 -iu Ethernet44 -iu Ethernet48 -iu Ethernet4 -iu Ethernet52 -iu Ethernet56 -iu Ethernet60 -iu Ethernet64 -iu Ethernet68 -iu Ethernet72 -iu Ethernet76 -iu Ethernet80 -iu Ethernet84 -iu Ethernet88 -iu Ethernet8 -iu Ethernet92 -iu Ethernet96
    override: replace
"""
        self.assertEqual(raw_str, expected_yaml)

        first_pass, second_pass = get_start_order(list(yaml_output.get("services", {}).keys()))
        self.assertEqual(first_pass, [
            'isc-dhcpv4-relay-Vlan1000',
            'isc-dhcpv4-relay-Vlan1200',
            'dhcp6relay'
        ])
        self.assertEqual(second_pass, [
            'dhcpmon-Vlan1000',
            'dhcpmon-Vlan1200'
        ])

if __name__ == '__main__':
    unittest.main()
