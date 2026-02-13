#!/bin/python3

import json
import subprocess
import sys
import ipaddress
import yaml
from typing import Dict, Any, Iterable, Tuple

LAYER_NAME = "dynamic_services"
TMP_CONFIG_FILE_PATH = "/tmp/pebble_dynamic_services.yaml"

def get_start_order(svc_name: list[str]) -> tuple[list[str], list[str]]:
    first_pass, second_pass = [], []
    for svc in svc_name:
        # Put all dhcpmon-* services in second pass
        if svc.startswith("dhcpmon-"):
            second_pass.append(svc)
        else:
            first_pass.append(svc)
    return first_pass, second_pass


def add_layer_and_replan(pebble_conf: Dict[str, Any]) -> None:
    with open(TMP_CONFIG_FILE_PATH, "w") as f:
        yaml.dump(pebble_conf, f, width=float("inf"))
    cmd_add = ["pebble", "add", LAYER_NAME, "--combine", TMP_CONFIG_FILE_PATH]
    subprocess.run(cmd_add, check=True)
    cmd_reload = ["pebble", "replan"]
    subprocess.run(cmd_reload, check=True)

    # Start all services in the new layer
    first_pass, second_pass = get_start_order(pebble_conf.get("services", {}).keys())
    for svc in first_pass:
        cmd_start = ["pebble", "start", svc]
        subprocess.run(cmd_start, check=True)
        
    for svc in second_pass:
        cmd_start = ["pebble", "start", svc]
        subprocess.run(cmd_start, check=True)


def fetch_cfg_var(var_name: str) -> Any:
    # Run `sonic-cfggen -d --var-json VAR` and return parsed JSON, or None on error.
    cmd = ["sonic-cfggen", "-d", "--var-json", var_name]
    try:
        out = subprocess.check_output(cmd, text=True)
        return json.loads(out)
    except Exception:
        return None


def is_ipv4(addr: str) -> bool:
    if not addr:
        return False
    # strip any surrounding whitespace and CIDR
    a = str(addr).strip().split("/")[0]
    try:
        ipaddress.IPv4Address(a)
        return True
    except Exception:
        return False


def is_ipv6(addr: str) -> bool:
    if not addr:
        return False
    # strip any surrounding whitespace and CIDR
    a = str(addr).strip().split("/")[0]
    try:
        ipaddress.IPv6Address(a)
        return True
    except Exception:
        return False

def pfx_filter(mapping: Dict[str, Any]) -> Iterable[Tuple[str, str]]:
    # Example input:
    #     "Vlan1000": {},
    #     "Vlan1000|10.242.21.1/24": {},
    if not mapping:
        return
    for key in mapping.keys():
        lst = key.split("|")
        if len(lst) != 2:
            continue
        vlan_name, addr = lst[0], lst[1]
        yield vlan_name, addr


def split_key(key: str) -> Tuple[str, str]:
    # Split a key of form 'Interface|Prefix' into (Interface, Prefix)
    parts = key.split("|", 1)
    if len(parts) != 2:
        return key, ""
    return parts[0], parts[1]
    
def get_primary_addrs(vlan_interface: Dict[str, Any]) -> set:
    # One vlan may have multiple primary addresses.
    out = set()
    intf_with_secondary = set()
    if not vlan_interface:
        return out
    for name, obj in vlan_interface.items():
        if 'secondary' in obj:
            vlan_name, network = split_key(name)
            intf_with_secondary.add(vlan_name)

    for name, obj in vlan_interface.items():
        vlan_name, network = split_key(name)
        if network == "":
            continue
        if vlan_name in intf_with_secondary and 'secondary' not in obj:
            addr = network.split("/")[0]
            out.add((vlan_name, addr))
    return out


def gen_dhcpv4_relay_agents(VLAN: Dict[str, Any], VLAN_INTERFACE: Dict[str, Any],
                            INTERFACE: Dict[str, Any], PORTCHANNEL_INTERFACE: Dict[str, Any],
                            DEVICE_METADATA: Dict[str, Any]) -> Dict[str, Any]:
    # dhcpv4-relay.agents.j2
    services = {}
    primary_addrs = get_primary_addrs(VLAN_INTERFACE or {})

    for vlan_name in (VLAN_INTERFACE or {}).keys():
        vlan_obj = VLAN.get(vlan_name)
        if not vlan_obj or 'dhcp_servers' not in vlan_obj or len(vlan_obj.get('dhcp_servers') or []) == 0:
            continue

        relay_for_ipv4 = False
        for dhcp_server in vlan_obj.get('dhcp_servers'):
            if is_ipv4(dhcp_server):
                relay_for_ipv4 = True
                break

        if not relay_for_ipv4:
            continue

        cmd = ["/usr/sbin/dhcrelay", "-d", "-m", "discard", "-a %h:%p", "%P", "--name-alias-map-file", "/tmp/port-name-alias-map.txt", "-id", vlan_name]

        try:
            md = DEVICE_METADATA or {}
            localhost = md.get('localhost', {})
            if 'subtype' in localhost and localhost.get('subtype') == 'DualToR':
                cmd.extend(["-U", "Loopback0", "-dt"])
            if localhost.get('deployment_id') == '8':
                cmd.append('-si')
        except Exception:
            pass

        # treat VLAN_INTERFACE as upstream (-iu), skip the vlan itself
        for name, addr in pfx_filter(VLAN_INTERFACE or {}):
            if name != vlan_name and is_ipv4(addr):
                cmd.extend(["-iu", name])
        for name, addr in pfx_filter(INTERFACE or {}):
            if is_ipv4(addr):
                cmd.extend(["-iu", name])
        for name, addr in pfx_filter(PORTCHANNEL_INTERFACE or {}):
            if is_ipv4(addr):
                cmd.extend(["-iu", name])

        for (name, gw) in primary_addrs:
            if name == vlan_name and is_ipv4(gw):
                cmd.extend(["-pg", gw])

        dhcp_servers = [str(s) for s in vlan_obj.get('dhcp_servers') if is_ipv4(s)]
        cmd_str = ' '.join(cmd)
        if dhcp_servers:
            cmd_str = cmd_str + ' ' + ' '.join(dhcp_servers)

        service_name = f"isc-dhcpv4-relay-{vlan_name}"
        services[service_name] = {
            "command": cmd_str,
            "override": "replace"
        }

    return services


def gen_dhcpv6_relay_agent(VLAN_INTERFACE: Dict[str, Any], DHCP_RELAY: Dict[str, Any], DEVICE_METADATA: Dict[str, Any]) -> Dict[str, Any]:
    relay_for_ipv6 = False
    services = {}
    for vlan_name in (VLAN_INTERFACE or {}).keys():
        dhcp_relay_obj = DHCP_RELAY.get(vlan_name) if DHCP_RELAY else None
        if dhcp_relay_obj and 'dhcpv6_servers' in dhcp_relay_obj and len(dhcp_relay_obj.get('dhcpv6_servers') or []) > 0:
            for dhcpv6_server in dhcp_relay_obj.get('dhcpv6_servers'):
                if is_ipv6(dhcpv6_server):
                    relay_for_ipv6 = True
                    break

    if relay_for_ipv6:
        services['dhcp6relay'] = {
            'command': '/usr/sbin/dhcp6relay',
            "override": "replace"
        }
        localhost = DEVICE_METADATA.get('localhost', {})
        if 'subtype' in localhost and localhost.get('subtype') == 'DualToR':
            services['dhcp6relay']['command'] += " -u Loopback0"

    return services


def gen_dhcp_relay_monitors(VLAN: Dict[str, Any], VLAN_INTERFACE: Dict[str, Any],
                            INTERFACE: Dict[str, Any], PORTCHANNEL_INTERFACE: Dict[str, Any],
                            DEVICE_METADATA: Dict[str, Any], DHCP_RELAY: Dict[str, Any],
                            MGMT_INTERFACE: Dict[str, Any] = None) -> Dict[str, Any]:
    # dhcp-relay.monitors.j2
    services = {}
    # Identify which VLANs need DHCP monitoring
    for vlan_name in (VLAN_INTERFACE or {}).keys():
        relay_for_ipv4, relay_for_ipv6 = False, False

        # Check DHCPv4 agents
        vlan_obj = VLAN.get(vlan_name) if VLAN else None
        if vlan_obj and 'dhcp_servers' in vlan_obj and len(vlan_obj.get('dhcp_servers') or []) > 0:
            for dhcp_server in vlan_obj.get('dhcp_servers'):
                if is_ipv4(dhcp_server):
                    relay_for_ipv4 = True
                    break

        # Check DHCPv6 agents
        dhcp_relay_obj = DHCP_RELAY.get(vlan_name) if DHCP_RELAY else None
        if dhcp_relay_obj and 'dhcpv6_servers' in dhcp_relay_obj and len(dhcp_relay_obj.get('dhcpv6_servers') or []) > 0:
            for dhcpv6_server in dhcp_relay_obj.get('dhcpv6_servers'):
                if is_ipv6(dhcpv6_server):
                    relay_for_ipv6 = True
                    break

        if relay_for_ipv4 or relay_for_ipv6:
            cmd = ["/usr/sbin/dhcpmon", "-id", vlan_name]
            try:
                md = DEVICE_METADATA or {}
                localhost = md.get('localhost', {})
                if 'subtype' in localhost and localhost.get('subtype') == 'DualToR':
                    cmd.extend(["-u", "Loopback0"])
            except Exception:
                pass

            # Treat all other VLAN interfaces as upstream (-iu)
            for name, addr in pfx_filter(VLAN_INTERFACE or {}):
                if name != vlan_name and is_ipv4(addr):
                    cmd.extend(["-iu", name])
            for name, addr in pfx_filter(INTERFACE or {}):
                if is_ipv4(addr):
                    cmd.extend(["-iu", name])
            for name, addr in pfx_filter(PORTCHANNEL_INTERFACE or {}):
                if is_ipv4(addr):
                    cmd.extend(["-iu", name])
            if MGMT_INTERFACE:
                for name, addr in pfx_filter(MGMT_INTERFACE or {}):
                    if is_ipv4(addr):
                        cmd.extend(["-im", name])
            
            cmd_str = ' '.join(cmd)
            service_name = f"dhcpmon-{vlan_name}"
            services[service_name] = {
                "command": cmd_str,
                "override": "replace"
            }

    return services


def gen_all_config(VLAN: Dict[str, Any], VLAN_INTERFACE: Dict[str, Any],
                   INTERFACE: Dict[str, Any], PORTCHANNEL_INTERFACE: Dict[str, Any],
                   DEVICE_METADATA: Dict[str, Any], DHCP_RELAY: Dict[str, Any],
                   MGMT_INTERFACE: Dict[str, Any] = None) -> Dict[str, Any]:
    if VLAN_INTERFACE is {}:
        return {}

    ipv4_num_relays, ipv6_num_relays = 0, 0
    for vlan_name in VLAN_INTERFACE.keys():
        if vlan_name in VLAN and 'dhcp_servers' in VLAN[vlan_name] and len(VLAN[vlan_name]['dhcp_servers']) > 0:
            ipv4_num_relays += 1
        if vlan_name in VLAN and 'dhcpv6_servers' in VLAN[vlan_name] and len(VLAN[vlan_name]['dhcpv6_servers']) > 0:
            ipv6_num_relays += 1

    if ipv4_num_relays == 0 and ipv6_num_relays == 0:
        return {}

    all_services = {}

    # {% include 'dhcpv4-relay.agents.j2' %} --> [program:isc-dhcpv4-relay-Vlanxxx]
    dhcpv4_services = gen_dhcpv4_relay_agents(VLAN, VLAN_INTERFACE, INTERFACE, PORTCHANNEL_INTERFACE, DEVICE_METADATA)
    all_services.update(dhcpv4_services)

    # {% include 'dhcpv6-relay.agents.j2' %} --> [program:dhcp6relay]
    dhcp6relay = gen_dhcpv6_relay_agent(VLAN_INTERFACE, DHCP_RELAY, DEVICE_METADATA)
    all_services.update(dhcp6relay)

    # {% include 'dhcp-relay.monitors.j2' %} --> [program:dhcpmon-Vlanxxx]
    monitor_services = gen_dhcp_relay_monitors(VLAN, VLAN_INTERFACE, INTERFACE, PORTCHANNEL_INTERFACE, DEVICE_METADATA, DHCP_RELAY, MGMT_INTERFACE)
    all_services.update(monitor_services)

    pebble_config = {
        "services": all_services
    }
    return pebble_config


def main():
    VLAN = fetch_cfg_var('VLAN') or {}
    VLAN_INTERFACE = fetch_cfg_var('VLAN_INTERFACE') or {}
    INTERFACE = fetch_cfg_var('INTERFACE') or {}
    PORTCHANNEL_INTERFACE = fetch_cfg_var('PORTCHANNEL_INTERFACE') or {}
    DEVICE_METADATA = fetch_cfg_var('DEVICE_METADATA') or {}
    DHCP_RELAY = fetch_cfg_var('DHCP_RELAY') or {}
    MGMT_INTERFACE = fetch_cfg_var('MGMT_INTERFACE') or {}

    # Generate and output pebble configuration
    services = gen_all_config(VLAN, VLAN_INTERFACE, INTERFACE, PORTCHANNEL_INTERFACE, DEVICE_METADATA, DHCP_RELAY, MGMT_INTERFACE)
    add_layer_and_replan(services)


if __name__ == '__main__':
    main()
