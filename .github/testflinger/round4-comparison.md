# SONiC VS 202405 — Comparison Report

## Runs Compared

| | **A: whomp ubuntu-sonic** | **B: polari official** |
|--|--|--|
| Directory | `5630d557-whomp-ubuntu` | `df91626e-polari-official` |
| Workers | 9 | 9 |

## Summary (adjusted, excl. VS-incompatible, AST total = 707)

| Metric | **A: whomp ubuntu-sonic** | **B: polari official** | Δ |
|--------|--|--|--|
| Dirs completed | 60 | 56 | -4 |
| Dirs incomplete | 1 | 2 | +1 |
| Dirs untested/not-run | 14 | 17 | +3 |
| ✅ Passed | 355 | 319 | -36 |
| ❌ Failed | 131 | 101 | -30 |
| ⚠️ Errors | 373 | 611 | +238 |
| ⏭️ Skipped | 148 | 669 | +521 |
| AST Total (denominator) | 707 | 707 | — |
| **Pass rate (passed/AST total)** | 50.2% | 45.1% |  |

## Per-Directory Comparison (VS-compatible only)

Legend: ✅=all pass, ❌=has failures/errors, ⏭️=all skipped, 💀=incomplete, 🚫=untested, ·=not in run

| Directory | A: Status | A: P/F/E | B: Status | B: P/F/E | Verdict |
|-----------|-----------|----------|-----------|----------|---------|
| `.` | ❌ | 4/0/1 | ✅ | 4/0/0 | 🔵 B better |
| `acl` | 💀 | — | ❌ | 0/25/400 | 🔵 B better |
| `acl/custom_acl_table` | ❌ | 0/0/1 | ❌ | 0/1/0 | 🟡 Both fail |
| `acl/null_route` | ❌ | 0/0/1 | ❌ | 0/1/0 | 🟡 Both fail |
| `arp` | ❌ | 6/6/1 | ❌ | 9/4/0 | 🔵 B better |
| `bgp` | ❌ | 20/1/0 | 💀 | — | 🟢 A better |
| `cacl` | ❌ | 6/1/2 | ❌ | 5/1/0 | 🟢 A better |
| `crm` | ❌ | 0/11/0 | ❌ | 4/7/1 | 🔵 B better |
| `database` | ✅ | 4/0/0 | ✅ | 4/0/0 | ✅ Both pass |
| `decap` | ❌ | 0/4/0 | · | — | 🟢 A better |
| `dhcp_relay` | ❌ | 12/6/0 | ✅ | 14/0/0 | 🔵 B better |
| `disk` | ❌ | 0/1/0 | ✅ | 1/0/0 | 🔵 B better |
| `dns` | · | — | ✅ | 1/0/0 | 🔵 B better |
| `dns/static_dns` | ❌ | 0/0/5 | ✅ | 3/0/0 | 🔵 B better |
| `dut_console` | ❌ | 0/1/4 | ⏭️ | 0/0/0 | 🔵 B better |
| `ecmp` | ❌ | 0/1/0 | ⏭️ | 0/0/0 | 🔵 B better |
| `ecmp/inner_hashing` | ❌ | 0/12/2 | ⏭️ | 0/0/0 | 🔵 B better |
| `fdb` | ✅ | 17/0/0 | ✅ | 17/0/0 | ✅ Both pass |
| `fib` | ❌ | 4/1/0 | ❌ | 3/2/0 | 🟢 A better |
| `generic_config_updater` | ❌ | 60/9/0 | ❌ | 59/9/12 | 🟢 A better |
| `gnmi` | ❌ | 0/0/6 | ✅ | 6/0/0 | 🔵 B better |
| `golden_config_infra` | ✅ | 1/0/0 | ✅ | 1/0/0 | ✅ Both pass |
| `hash` | ❌ | 2/5/0 | ❌ | 1/2/0 | 🟢 A better |
| `http` | ✅ | 1/0/0 | ⏭️ | 0/0/0 | 🟢 A better |
| `iface_loopback_action` | ❌ | 0/3/0 | ⏭️ | 0/0/0 | 🔵 B better |
| `iface_namingmode` | ✅ | 38/0/0 | · | — | 🟢 A better |
| `ip` | ❌ | 0/8/10 | · | — | 🟢 A better |
| `ipfwd` | ❌ | 1/1/0 | ❌ | 1/1/0 | 🟡 Both fail |
| `lldp` | ❌ | 0/0/7 | ✅ | 7/0/0 | 🔵 B better |
| `log_fidelity` | ❌ | 0/1/0 | ✅ | 1/0/0 | 🔵 B better |
| `memory_checker` | ❌ | 0/0/4 | ✅ | 4/0/0 | 🔵 B better |
| `minigraph` | · | — | ✅ | 1/0/0 | 🔵 B better |
| `monit` | ✅ | 1/0/0 | ✅ | 1/0/0 | ✅ Both pass |
| `mvrf` | ❌ | 5/4/0 | ❌ | 5/4/0 | 🟡 Both fail |
| `ntp` | ✅ | 6/0/0 | ✅ | 6/0/0 | ✅ Both pass |
| `override_config_table` | ✅ | 1/0/0 | ✅ | 1/0/0 | ✅ Both pass |
| `passw_hardening` | ✅ | 10/0/0 | ✅ | 10/0/0 | ✅ Both pass |
| `pc` | ❌ | 6/2/0 | ❌ | 6/1/0 | 🔵 B better |
| `pfc_asym` | ❌ | 0/0/4 | · | — | 🟢 A better |
| `platform_tests` | ❌ | 12/11/11 | ❌ | 10/12/16 | 🟢 A better |
| `platform_tests/cli` | ❌ | 2/7/0 | ❌ | 3/6/0 | 🔵 B better |
| `platform_tests/counterpoll` | ✅ | 1/0/0 | ✅ | 1/0/0 | ✅ Both pass |
| `platform_tests/fwutil` | · | — | ⏭️ | 0/0/0 | 🔵 B better |
| `platform_tests/link_flap` | ❌ | 0/1/0 | ❌ | 0/1/0 | 🟡 Both fail |
| `platform_tests/sfp` | ❌ | 5/4/2 | ❌ | 5/4/2 | 🟡 Both fail |
| `portstat` | ✅ | 21/0/0 | ✅ | 21/0/0 | ✅ Both pass |
| `process_monitoring` | ❌ | 0/2/0 | ✅ | 2/0/0 | 🔵 B better |
| `qos` | ❌ | 1/3/240 | ❌ | 1/1/155 | 🔵 B better |
| `radv` | ✅ | 6/0/0 | · | — | 🟢 A better |
| `reset_factory` | ❌ | 0/4/0 | ⏭️ | 0/0/0 | 🔵 B better |
| `route` | ✅ | 19/0/0 | ✅ | 18/0/0 | ✅ Both pass |
| `scp` | ✅ | 1/0/0 | ✅ | 1/0/0 | ✅ Both pass |
| `show_techsupport` | ❌ | 5/3/2 | ✅ | 7/0/0 | 🔵 B better |
| `snmp` | ❌ | 14/4/5 | ❌ | 16/2/7 | 🔵 B better |
| `span` | ❌ | 0/4/0 | ❌ | 0/4/0 | 🟡 Both fail |
| `ssh` | ❌ | 10/1/0 | 💀 | — | 🟢 A better |
| `stress` | ✅ | 1/0/0 | · | — | 🟢 A better |
| `sub_port_interfaces` | ❌ | 0/0/36 | ❌ | 7/8/16 | 🔵 B better |
| `syslog` | ❌ | 12/1/16 | · | — | 🟢 A better |
| `system_health` | ❌ | 1/4/3 | ❌ | 2/3/2 | 🔵 B better |
| `tacacs` | ❌ | 24/3/0 | ❌ | 26/1/0 | 🔵 B better |
| `telemetry` | ❌ | 14/1/0 | ✅ | 15/0/0 | 🔵 B better |
| `testbed_setup` | ✅ | 1/0/0 | ✅ | 1/0/0 | ✅ Both pass |
| `vlan` | ❌ | 0/0/10 | ✅ | 6/0/0 | 🔵 B better |
| `vxlan` | · | — | ❌ | 2/1/0 | 🔵 B better |

## Score Summary

| Category | Count | Directories |
|----------|-------|-------------|
| 🟢 **A better** (whomp ubuntu-sonic) | 15 | `bgp`, `cacl`, `decap`, `fib`, `generic_config_updater`, `hash`, `http`, `iface_namingmode`, `ip`, `pfc_asym`, `platform_tests`, `radv`, `ssh`, `stress`, `syslog` |
| 🔵 **B better** (polari official) | 31 | `.`, `acl`, `arp`, `crm`, `dhcp_relay`, `disk`, `dns`, `dns/static_dns`, `dut_console`, `ecmp`, `ecmp/inner_hashing`, `gnmi`, `iface_loopback_action`, `lldp`, `log_fidelity`, `memory_checker`, `minigraph`, `pc`, `platform_tests/cli`, `platform_tests/fwutil`... |
| ✅ Both pass / same | 19 | `acl/custom_acl_table`, `acl/null_route`, `database`, `fdb`, `golden_config_infra`, `ipfwd`, `monit`, `mvrf`, `ntp`, `override_config_table`, `passw_hardening`, `platform_tests/counterpoll`, `platform_tests/link_flap`, `platform_tests/sfp`, `portstat`, `route`, `scp`, `span`, `testbed_setup` |
| Only in A | 0 |  |
| Only in B | 0 |  |

## Key Flips (pass↔fail between runs)

### `.` — ✅ in B, ❌ in A

| | A (whomp ubuntu-sonic) | B (polari official) |
|--|--|--|
| Passed | 4 | 4 |
| Failed | 0 | 0 |
| Errors | 1 | 0 |

Failures in whomp ubuntu-sonic:
- ⚠️ `test_pktgen.py::test_pktgen[vlab-01-None]`

### `dhcp_relay` — ✅ in B, ❌ in A

| | A (whomp ubuntu-sonic) | B (polari official) |
|--|--|--|
| Passed | 12 | 14 |
| Failed | 6 | 0 |
| Errors | 0 | 0 |

Failures in whomp ubuntu-sonic:
- ❌ `dhcp_relay/test_dhcp_relay.py::test_dhcp_relay_default`
- ❌ `dhcp_relay/test_dhcp_relay_stress.py::test_dhcp_relay_stress[discover]`
- ❌ `dhcp_relay/test_dhcp_relay_stress.py::test_dhcp_relay_stress[offer]`
- ❌ `dhcp_relay/test_dhcp_relay_stress.py::test_dhcp_relay_stress[request]`
- ❌ `dhcp_relay/test_dhcp_relay_stress.py::test_dhcp_relay_stress[ack]`
- ❌ `dhcp_relay/test_dhcpv6_relay.py::test_interface_binding`

### `disk` — ✅ in B, ❌ in A

| | A (whomp ubuntu-sonic) | B (polari official) |
|--|--|--|
| Passed | 0 | 1 |
| Failed | 1 | 0 |
| Errors | 0 | 0 |

Failures in whomp ubuntu-sonic:
- ❌ `disk/test_disk_exhaustion.py::test_disk_exhaustion`

### `dns/static_dns` — ✅ in B, ❌ in A

| | A (whomp ubuntu-sonic) | B (polari official) |
|--|--|--|
| Passed | 0 | 3 |
| Failed | 0 | 0 |
| Errors | 5 | 0 |

Failures in whomp ubuntu-sonic:
- ⚠️ `dns/static_dns/test_static_dns.py::test_static_dns_basic`
- ⚠️ `dns/static_dns/test_static_dns.py::TestStaticMgmtPortIP::test_dynamic_dns_not_working_when_static_ip_configured`
- ⚠️ `dns/static_dns/test_static_dns.py::TestDynamicMgmtPortIP::test_static_dns_is_not_changing_when_do_dhcp_renew`
- ⚠️ `dns/static_dns/test_static_dns.py::TestDynamicMgmtPortIP::test_dynamic_dns_working_when_no_static_ip_and_static_dns`
- ⚠️ `dns/static_dns/test_static_dns.py::test_static_dns_negative`

### `gnmi` — ✅ in B, ❌ in A

| | A (whomp ubuntu-sonic) | B (polari official) |
|--|--|--|
| Passed | 0 | 6 |
| Failed | 0 | 0 |
| Errors | 6 | 0 |

Failures in whomp ubuntu-sonic:
- ⚠️ `gnmi/test_gnmi.py::test_gnmi_capabilities`
- ⚠️ `gnmi/test_gnmi.py::test_gnmi_authorize_failed_with_invalid_cname`
- ⚠️ `gnmi/test_gnmi_appldb.py::test_gnmi_appldb_01`
- ⚠️ `gnmi/test_gnmi_configdb.py::test_gnmi_configdb_incremental_01`
- ⚠️ `gnmi/test_gnmi_configdb.py::test_gnmi_configdb_incremental_02`
- ⚠️ `gnmi/test_gnmi_configdb.py::test_gnmi_configdb_full_01`

### `lldp` — ✅ in B, ❌ in A

| | A (whomp ubuntu-sonic) | B (polari official) |
|--|--|--|
| Passed | 0 | 7 |
| Failed | 0 | 0 |
| Errors | 7 | 0 |

Failures in whomp ubuntu-sonic:
- ⚠️ `lldp/test_lldp.py::test_lldp[vlab-01-None]`
- ⚠️ `lldp/test_lldp.py::test_lldp_neighbor[vlab-01-None]`
- ⚠️ `lldp/test_lldp_syncd.py::test_lldp_entry_table_keys[vlab-01]`
- ⚠️ `lldp/test_lldp_syncd.py::test_lldp_entry_table_content[vlab-01]`
- ⚠️ `lldp/test_lldp_syncd.py::test_lldp_entry_table_after_flap[vlab-01]`
- ⚠️ `lldp/test_lldp_syncd.py::test_lldp_entry_table_after_lldp_restart[vlab-01]`
- ⚠️ `lldp/test_lldp_syncd.py::test_lldp_entry_table_after_reboot[vlab-01]`

### `log_fidelity` — ✅ in B, ❌ in A

| | A (whomp ubuntu-sonic) | B (polari official) |
|--|--|--|
| Passed | 0 | 1 |
| Failed | 1 | 0 |
| Errors | 0 | 0 |

Failures in whomp ubuntu-sonic:
- ❌ `log_fidelity/test_bgp_shutdown.py::test_bgp_shutdown[vlab-01]`

### `memory_checker` — ✅ in B, ❌ in A

| | A (whomp ubuntu-sonic) | B (polari official) |
|--|--|--|
| Passed | 0 | 4 |
| Failed | 0 | 0 |
| Errors | 4 | 0 |

Failures in whomp ubuntu-sonic:
- ⚠️ `memory_checker/test_memory_checker.py::test_memory_checker[vlab-01-]`
- ⚠️ `memory_checker/test_memory_checker.py::test_memory_checker_recover[vlab-01-]`
- ⚠️ `memory_checker/test_memory_checker.py::test_monit_reset_counter_failure[vlab-01-]`
- ⚠️ `memory_checker/test_memory_checker.py::test_memory_checker_without_container_created[vlab-01-]`

### `process_monitoring` — ✅ in B, ❌ in A

| | A (whomp ubuntu-sonic) | B (polari official) |
|--|--|--|
| Passed | 0 | 2 |
| Failed | 2 | 0 |
| Errors | 0 | 0 |

Failures in whomp ubuntu-sonic:
- ❌ `process_monitoring/test_critical_process_monitoring.py::test_monitoring_critical_processes`
- ❌ `process_monitoring/test_critical_process_monitoring.py::test_orchagent_heartbeat`

### `show_techsupport` — ✅ in B, ❌ in A

| | A (whomp ubuntu-sonic) | B (polari official) |
|--|--|--|
| Passed | 5 | 7 |
| Failed | 3 | 0 |
| Errors | 2 | 0 |

Failures in whomp ubuntu-sonic:
- ⚠️ `show_techsupport/test_techsupport.py::test_techsupport[acl-vlab-01]`
- ⚠️ `show_techsupport/test_techsupport.py::test_techsupport[mirroring-vlab-01]`
- ❌ `show_techsupport/test_auto_techsupport.py::TestAutoTechSupport::test_sanity`
- ❌ `show_techsupport/test_auto_techsupport.py::TestAutoTechSupport::test_rate_limit_interval`
- ❌ `show_techsupport/test_auto_techsupport.py::TestAutoTechSupport::test_sai_sdk_dump`

### `telemetry` — ✅ in B, ❌ in A

| | A (whomp ubuntu-sonic) | B (polari official) |
|--|--|--|
| Passed | 14 | 15 |
| Failed | 1 | 0 |
| Errors | 0 | 0 |

Failures in whomp ubuntu-sonic:
- ❌ `telemetry/test_events.py::test_events[vlab-01-False]`

### `vlan` — ✅ in B, ❌ in A

| | A (whomp ubuntu-sonic) | B (polari official) |
|--|--|--|
| Passed | 0 | 6 |
| Failed | 0 | 0 |
| Errors | 10 | 0 |

Failures in whomp ubuntu-sonic:
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


## Both-Fail Directories — Detailed Comparison

| Directory | A: P/F/E | B: P/F/E | Δ Passed | Δ Failed |
|-----------|----------|----------|----------|----------|
| `acl/custom_acl_table` | 0/0/1 | 0/1/0 | 0 | +1 |
| `acl/null_route` | 0/0/1 | 0/1/0 | 0 | +1 |
| `arp` | 6/6/1 | 9/4/0 | +3 | -2 |
| `cacl` | 6/1/2 | 5/1/0 | -1 | 0 |
| `crm` | 0/11/0 | 4/7/1 | +4 | -4 |
| `fib` | 4/1/0 | 3/2/0 | -1 | +1 |
| `generic_config_updater` | 60/9/0 | 59/9/12 | -1 | 0 |
| `hash` | 2/5/0 | 1/2/0 | -1 | -3 |
| `ipfwd` | 1/1/0 | 1/1/0 | 0 | 0 |
| `mvrf` | 5/4/0 | 5/4/0 | 0 | 0 |
| `pc` | 6/2/0 | 6/1/0 | 0 | -1 |
| `platform_tests` | 12/11/11 | 10/12/16 | -2 | +1 |
| `platform_tests/cli` | 2/7/0 | 3/6/0 | +1 | -1 |
| `platform_tests/link_flap` | 0/1/0 | 0/1/0 | 0 | 0 |
| `platform_tests/sfp` | 5/4/2 | 5/4/2 | 0 | 0 |
| `qos` | 1/3/240 | 1/1/155 | 0 | -2 |
| `snmp` | 14/4/5 | 16/2/7 | +2 | -2 |
| `span` | 0/4/0 | 0/4/0 | 0 | 0 |
| `sub_port_interfaces` | 0/0/36 | 7/8/16 | +7 | +8 |
| `system_health` | 1/4/3 | 2/3/2 | +1 | -1 |
| `tacacs` | 24/3/0 | 26/1/0 | +2 | -2 |

## Coverage-Only Directories

These directories were completed by only one run.

### A only — whomp ubuntu-sonic (9 dirs, 87 extra passed)

| Directory | P/F/E | Note |
|-----------|-------|------|
| `iface_namingmode` | 38/0/0 | ✅ all pass |
| `bgp` | 20/1/0 |  |
| `syslog` | 12/1/16 |  |
| `ssh` | 10/1/0 |  |
| `radv` | 6/0/0 | ✅ all pass |
| `stress` | 1/0/0 | ✅ all pass |
| `decap` | 0/4/0 |  |
| `ip` | 0/8/10 |  |
| `pfc_asym` | 0/0/4 |  |

### B only — polari official (5 dirs, 4 extra passed)

| Directory | P/F/E | Note |
|-----------|-------|------|
| `vxlan` | 2/1/0 |  |
| `dns` | 1/0/0 | ✅ all pass |
| `minigraph` | 1/0/0 | ✅ all pass |
| `acl` | 0/25/400 |  |
| `platform_tests/fwutil` | 0/0/0 |  |

