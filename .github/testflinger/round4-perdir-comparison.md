# SONiC VS 202405 — Per-Directory Fair Comparison

> **Methodology**: Only directories where **both** runs completed are compared.
> This eliminates coverage bias and focuses on actual test quality.
> Pass rate = passed / AST total (for common dirs only).

## Runs Compared

| | **A: whomp ubuntu-sonic** | **B: polari official** |
|--|--|--|
| Directory | `5630d557-whomp-ubuntu` | `df91626e-polari-official` |
| Workers | 9 | 9 |
| Common completed dirs | 51 | 51 |
| AST total (common dirs) | 514 | 514 |

## Summary

| Metric | **A (whomp ubuntu-sonic)** | **B (polari official)** | Δ (B−A) |
|--------|:-:|:-:|:-:|
| ✅ Passed | 268 | 315 | +47 |
| ❌ Failed | 116 | 75 | -41 |
| ⚠️ Errors | 343 | 211 | -132 |
| ⏭️ Skipped | 120 | 246 | +126 |
| **Pass rate** | **52.1%** | **61.3%** | **+9.1%** |

## Directory Score Summary

| Category | Count |
|----------|:-----:|
| 🅰️ A wins (A all-pass, B has failures) | 1 |
| 🅱️ B wins (B all-pass, A has failures) | 12 |
| 🤝 Both pass | 12 |
| Both fail — A fewer failures | 3 |
| Both fail — B fewer failures | 10 |
| Both fail — tie | 8 |
| Other | 5 |
| **Total A advantage** | **4** |
| **Total B advantage** | **22** |
| **Ties / both pass** | **25** |

## Per-Directory Comparison

| # | Directory | AST | A: P/F/E | B: P/F/E | Verdict |
|:-:|-----------|:---:|----------|----------|---------|
| 1 | `(root)` | 5 | 4/0/1 | 4/0/0 | 🅱️ B wins |
| 2 | `acl/custom_acl_table` | 1 | 0/0/1 | 0/1/0 | 🤝 Tie |
| 3 | `acl/null_route` | 1 | 0/0/1 | 0/1/0 | 🤝 Tie |
| 4 | `arp` | 10 | 6/6/1 | 9/4/0 | 🅱️ B better |
| 5 | `cacl` | 8 | 6/1/2 | 5/1/0 | 🅱️ B better |
| 6 | `crm` | 11 | 0/11/0 | 4/7/1 | 🅱️ B better |
| 7 | `database` | 4 | 4/0/0 | 4/0/0 | 🤝 Both pass |
| 8 | `dhcp_relay` | 18 | 12/6/0 | 14/0/0 | 🅱️ B wins |
| 9 | `disk` | 1 | 0/1/0 | 1/0/0 | 🅱️ B wins |
| 10 | `dns/static_dns` | 5 | 0/0/5 | 3/0/0 | 🅱️ B wins |
| 11 | `dut_console` | 5 | 0/1/4 | 0/0/0 | — |
| 12 | `ecmp` | 11 | 0/1/0 | 0/0/0 | — |
| 13 | `ecmp/inner_hashing` | 6 | 0/12/2 | 0/0/0 | — |
| 14 | `fdb` | 6 | 17/0/0 | 17/0/0 | 🤝 Both pass |
| 15 | `fib` | 4 | 4/1/0 | 3/2/0 | 🅰️ A better |
| 16 | `generic_config_updater` | 74 | 60/9/0 | 59/9/12 | 🅰️ A better |
| 17 | `gnmi` | 6 | 0/0/6 | 6/0/0 | 🅱️ B wins |
| 18 | `golden_config_infra` | 1 | 1/0/0 | 1/0/0 | 🤝 Both pass |
| 19 | `hash` | 10 | 2/5/0 | 1/2/0 | 🅱️ B better |
| 20 | `http` | 1 | 1/0/0 | 0/0/0 | 🅰️ A wins |
| 21 | `iface_loopback_action` | 3 | 0/3/0 | 0/0/0 | — |
| 22 | `ipfwd` | 2 | 1/1/0 | 1/1/0 | 🤝 Tie |
| 23 | `lldp` | 7 | 0/0/7 | 7/0/0 | 🅱️ B wins |
| 24 | `log_fidelity` | 1 | 0/1/0 | 1/0/0 | 🅱️ B wins |
| 25 | `memory_checker` | 5 | 0/0/4 | 4/0/0 | 🅱️ B wins |
| 26 | `monit` | 2 | 1/0/0 | 1/0/0 | 🤝 Both pass |
| 27 | `mvrf` | 9 | 5/4/0 | 5/4/0 | 🤝 Tie |
| 28 | `ntp` | 3 | 6/0/0 | 6/0/0 | 🤝 Both pass |
| 29 | `override_config_table` | 1 | 1/0/0 | 1/0/0 | 🤝 Both pass |
| 30 | `passw_hardening` | 10 | 10/0/0 | 10/0/0 | 🤝 Both pass |
| 31 | `pc` | 20 | 6/2/0 | 6/1/0 | 🅱️ B better |
| 32 | `platform_tests` | 46 | 12/11/11 | 10/12/16 | 🅰️ A better |
| 33 | `platform_tests/cli` | 10 | 2/7/0 | 3/6/0 | 🅱️ B better |
| 34 | `platform_tests/counterpoll` | 1 | 1/0/0 | 1/0/0 | 🤝 Both pass |
| 35 | `platform_tests/link_flap` | 2 | 0/1/0 | 0/1/0 | 🤝 Tie |
| 36 | `platform_tests/sfp` | 11 | 5/4/2 | 5/4/2 | 🤝 Tie |
| 37 | `portstat` | 21 | 21/0/0 | 21/0/0 | 🤝 Both pass |
| 38 | `process_monitoring` | 2 | 0/2/0 | 2/0/0 | 🅱️ B wins |
| 39 | `qos` | 34 | 1/3/240 | 1/1/155 | 🅱️ B better |
| 40 | `reset_factory` | 4 | 0/4/0 | 0/0/0 | — |
| 41 | `route` | 17 | 19/0/0 | 18/0/0 | 🤝 Both pass |
| 42 | `scp` | 1 | 1/0/0 | 1/0/0 | 🤝 Both pass |
| 43 | `show_techsupport` | 8 | 5/3/2 | 7/0/0 | 🅱️ B wins |
| 44 | `snmp` | 26 | 14/4/5 | 16/2/7 | 🅱️ B better |
| 45 | `span` | 4 | 0/4/0 | 0/4/0 | 🤝 Tie |
| 46 | `sub_port_interfaces` | 15 | 0/0/36 | 7/8/16 | 🅱️ B better |
| 47 | `system_health` | 8 | 1/4/3 | 2/3/2 | 🅱️ B better |
| 48 | `tacacs` | 27 | 24/3/0 | 26/1/0 | 🅱️ B better |
| 49 | `telemetry` | 15 | 14/1/0 | 15/0/0 | 🅱️ B wins |
| 50 | `testbed_setup` | 1 | 1/0/0 | 1/0/0 | 🤝 Both pass |
| 51 | `vlan` | 10 | 0/0/10 | 6/0/0 | 🅱️ B wins |

## Official Wins — Details

Directories where B passes 100% but A has failures:

### `(root)`
- A: 4P / 0F / 1E
- B: all pass (4P)
- A failures:
  - ⚠️ `test_pktgen.py::test_pktgen[vlab-01-None]`

### `dhcp_relay`
- A: 12P / 6F / 0E
- B: all pass (14P)
- A failures:
  - ❌ `dhcp_relay/test_dhcp_relay.py::test_dhcp_relay_default`
  - ❌ `dhcp_relay/test_dhcp_relay_stress.py::test_dhcp_relay_stress[discover]`
  - ❌ `dhcp_relay/test_dhcp_relay_stress.py::test_dhcp_relay_stress[offer]`
  - ❌ `dhcp_relay/test_dhcp_relay_stress.py::test_dhcp_relay_stress[request]`
  - ❌ `dhcp_relay/test_dhcp_relay_stress.py::test_dhcp_relay_stress[ack]`
  - ❌ `dhcp_relay/test_dhcpv6_relay.py::test_interface_binding`

### `disk`
- A: 0P / 1F / 0E
- B: all pass (1P)
- A failures:
  - ❌ `disk/test_disk_exhaustion.py::test_disk_exhaustion`

### `dns/static_dns`
- A: 0P / 0F / 5E
- B: all pass (3P)
- A failures:
  - ⚠️ `dns/static_dns/test_static_dns.py::test_static_dns_basic`
  - ⚠️ `dns/static_dns/test_static_dns.py::TestStaticMgmtPortIP::test_dynamic_dns_not_working_when_static_ip_configured`
  - ⚠️ `dns/static_dns/test_static_dns.py::TestDynamicMgmtPortIP::test_static_dns_is_not_changing_when_do_dhcp_renew`
  - ⚠️ `dns/static_dns/test_static_dns.py::TestDynamicMgmtPortIP::test_dynamic_dns_working_when_no_static_ip_and_static_dns`
  - ⚠️ `dns/static_dns/test_static_dns.py::test_static_dns_negative`

### `gnmi`
- A: 0P / 0F / 6E
- B: all pass (6P)
- A failures:
  - ⚠️ `gnmi/test_gnmi.py::test_gnmi_capabilities`
  - ⚠️ `gnmi/test_gnmi.py::test_gnmi_authorize_failed_with_invalid_cname`
  - ⚠️ `gnmi/test_gnmi_appldb.py::test_gnmi_appldb_01`
  - ⚠️ `gnmi/test_gnmi_configdb.py::test_gnmi_configdb_incremental_01`
  - ⚠️ `gnmi/test_gnmi_configdb.py::test_gnmi_configdb_incremental_02`
  - ⚠️ `gnmi/test_gnmi_configdb.py::test_gnmi_configdb_full_01`

### `lldp`
- A: 0P / 0F / 7E
- B: all pass (7P)
- A failures:
  - ⚠️ `lldp/test_lldp.py::test_lldp[vlab-01-None]`
  - ⚠️ `lldp/test_lldp.py::test_lldp_neighbor[vlab-01-None]`
  - ⚠️ `lldp/test_lldp_syncd.py::test_lldp_entry_table_keys[vlab-01]`
  - ⚠️ `lldp/test_lldp_syncd.py::test_lldp_entry_table_content[vlab-01]`
  - ⚠️ `lldp/test_lldp_syncd.py::test_lldp_entry_table_after_flap[vlab-01]`
  - ⚠️ `lldp/test_lldp_syncd.py::test_lldp_entry_table_after_lldp_restart[vlab-01]`
  - ⚠️ `lldp/test_lldp_syncd.py::test_lldp_entry_table_after_reboot[vlab-01]`

### `log_fidelity`
- A: 0P / 1F / 0E
- B: all pass (1P)
- A failures:
  - ❌ `log_fidelity/test_bgp_shutdown.py::test_bgp_shutdown[vlab-01]`

### `memory_checker`
- A: 0P / 0F / 4E
- B: all pass (4P)
- A failures:
  - ⚠️ `memory_checker/test_memory_checker.py::test_memory_checker[vlab-01-]`
  - ⚠️ `memory_checker/test_memory_checker.py::test_memory_checker_recover[vlab-01-]`
  - ⚠️ `memory_checker/test_memory_checker.py::test_monit_reset_counter_failure[vlab-01-]`
  - ⚠️ `memory_checker/test_memory_checker.py::test_memory_checker_without_container_created[vlab-01-]`

### `process_monitoring`
- A: 0P / 2F / 0E
- B: all pass (2P)
- A failures:
  - ❌ `process_monitoring/test_critical_process_monitoring.py::test_monitoring_critical_processes`
  - ❌ `process_monitoring/test_critical_process_monitoring.py::test_orchagent_heartbeat`

### `show_techsupport`
- A: 5P / 3F / 2E
- B: all pass (7P)
- A failures:
  - ⚠️ `show_techsupport/test_techsupport.py::test_techsupport[acl-vlab-01]`
  - ⚠️ `show_techsupport/test_techsupport.py::test_techsupport[mirroring-vlab-01]`
  - ❌ `show_techsupport/test_auto_techsupport.py::TestAutoTechSupport::test_sanity`
  - ❌ `show_techsupport/test_auto_techsupport.py::TestAutoTechSupport::test_rate_limit_interval`
  - ❌ `show_techsupport/test_auto_techsupport.py::TestAutoTechSupport::test_sai_sdk_dump`

### `telemetry`
- A: 14P / 1F / 0E
- B: all pass (15P)
- A failures:
  - ❌ `telemetry/test_events.py::test_events[vlab-01-False]`

### `vlan`
- A: 0P / 0F / 10E
- B: all pass (6P)
- A failures:
  - ⚠️ `vlan/test_autostate_disabled.py::TestAutostateDisabled::test_autostate_disabled[vlab-01]`
  - ⚠️ `vlan/test_host_vlan.py::test_host_vlan_no_floodling`
  - ⚠️ `vlan/test_vlan.py::test_vlan_tc1_send_untagged`
  - ⚠️ `vlan/test_vlan.py::test_vlan_tc2_send_tagged`
  - ⚠️ `vlan/test_vlan.py::test_vlan_tc3_send_invalid_vid`
  - ⚠️ `vlan/test_vlan.py::test_vlan_tc4_tagged_unicast`
  - ⚠️ `vlan/test_vlan.py::test_vlan_tc5_untagged_unicast`
  - ⚠️ `vlan/test_vlan.py::test_vlan_tc6_tagged_untagged_unicast`
  - ⚠️ `vlan/test_vlan.py::test_vlan_tc7_tagged_qinq_switch_on_outer_tag`
  - ⚠️ `vlan/test_vlan_ping.py::test_vlan_ping`

## Ubuntu-sonic Wins — Details

Directories where A passes 100% but B has failures:

### `http`
- A: all pass (1P)
- B: 0P / 0F / 0E

## Both-Fail Directories — Detailed Comparison

| Directory | A: P/F/E | B: P/F/E | Δ Passed | Δ Fail+Err | Better |
|-----------|----------|----------|:--------:|:----------:|--------|
| `acl/custom_acl_table` | 0/0/1 | 0/1/0 | 0 | 0 | 🤝 |
| `acl/null_route` | 0/0/1 | 0/1/0 | 0 | 0 | 🤝 |
| `arp` | 6/6/1 | 9/4/0 | +3 | -3 | 🅱️ B |
| `cacl` | 6/1/2 | 5/1/0 | -1 | -2 | 🅱️ B |
| `crm` | 0/11/0 | 4/7/1 | +4 | -3 | 🅱️ B |
| `fib` | 4/1/0 | 3/2/0 | -1 | +1 | 🅰️ A |
| `generic_config_updater` | 60/9/0 | 59/9/12 | -1 | +12 | 🅰️ A |
| `hash` | 2/5/0 | 1/2/0 | -1 | -3 | 🅱️ B |
| `ipfwd` | 1/1/0 | 1/1/0 | 0 | 0 | 🤝 |
| `mvrf` | 5/4/0 | 5/4/0 | 0 | 0 | 🤝 |
| `pc` | 6/2/0 | 6/1/0 | 0 | -1 | 🅱️ B |
| `platform_tests` | 12/11/11 | 10/12/16 | -2 | +6 | 🅰️ A |
| `platform_tests/cli` | 2/7/0 | 3/6/0 | +1 | -1 | 🅱️ B |
| `platform_tests/link_flap` | 0/1/0 | 0/1/0 | 0 | 0 | 🤝 |
| `platform_tests/sfp` | 5/4/2 | 5/4/2 | 0 | 0 | 🤝 |
| `qos` | 1/3/240 | 1/1/155 | 0 | -87 | 🅱️ B |
| `snmp` | 14/4/5 | 16/2/7 | +2 | 0 | 🤝 |
| `span` | 0/4/0 | 0/4/0 | 0 | 0 | 🤝 |
| `sub_port_interfaces` | 0/0/36 | 7/8/16 | +7 | -12 | 🅱️ B |
| `system_health` | 1/4/3 | 2/3/2 | +1 | -2 | 🅱️ B |
| `tacacs` | 24/3/0 | 26/1/0 | +2 | -2 | 🅱️ B |

## Coverage-Only Directories (excluded from comparison)

These directories were completed by only one run.

### A only (9 dirs, 87 extra passed)

- `bgp`: 20P/1F/0E
- `decap`: 0P/4F/0E
- `iface_namingmode`: 38P/0F/0E
- `ip`: 0P/8F/10E
- `pfc_asym`: 0P/0F/4E
- `radv`: 6P/0F/0E
- `ssh`: 10P/1F/0E
- `stress`: 1P/0F/0E
- `syslog`: 12P/1F/16E

### B only (5 dirs, 4 extra passed)

- `acl`: 0P/25F/400E
- `dns`: 1P/0F/0E
- `minigraph`: 1P/0F/0E
- `platform_tests/fwutil`: 0P/0F/0E
- `vxlan`: 2P/1F/0E

## Conclusion

When comparing only the **51 directories** where both runs completed:

- **polari official** achieves **61.3%** pass rate vs whomp ubuntu-sonic **52.1%** (+9.1%)
- Directory wins: A **4** vs B **22**, ties **25**
- A completed **9 additional dirs** (not in B), contributing **87 extra passed** tests
- B completed **5 additional dirs** (not in A), contributing **4 extra passed** tests

