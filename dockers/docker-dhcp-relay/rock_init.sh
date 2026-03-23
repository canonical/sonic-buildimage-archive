#!/usr/bin/env bash

source /usr/share/sonic/templates/envs

LAYER_FILE="/usr/share/sonic/templates/syslog-layer.yaml"
pebble add syslog-layer --combine $LAYER_FILE
pebble replan

# Generate supervisord config file
mkdir -p /etc/supervisor/conf.d/

# Generate the following files from templates:
# 1. supervisord configuration 
# 2. wait_for_intf.sh, which waits for all interfaces to come up
# 3. port-to-alias name map
CFGGEN_PARAMS=" \
    -d \
    -t /usr/share/sonic/templates/docker-dhcp-relay.supervisord.conf.j2,/etc/supervisor/conf.d/docker-dhcp-relay.supervisord.conf \
    -t /usr/share/sonic/templates/wait_for_intf.sh.j2,/usr/bin/wait_for_intf.sh \
    -t /usr/share/sonic/templates/port-name-alias-map.txt.j2,/tmp/port-name-alias-map.txt \
"
sonic-cfggen $CFGGEN_PARAMS

# Make the script that waits for all interfaces to come up executable
chmod +x /usr/bin/wait_for_intf.sh

# ============= Below is previous start.sh ======================
if [ "${RUNTIME_OWNER}" == "" ]; then
    RUNTIME_OWNER="kube"
fi

CTR_SCRIPT="/usr/share/sonic/scripts/container_startup.py"
if test -f ${CTR_SCRIPT}
then
    ${CTR_SCRIPT} -f dhcp_relay -o ${RUNTIME_OWNER} -v ${IMAGE_VERSION}
fi

TZ=$(cat /etc/timezone)
rm -rf /etc/localtime
ln -sf /usr/share/zoneinfo/$TZ /etc/localtime

# If pebble has dhcp relay agent services...
AGENTSERVICESV4=$(pebble services | grep -c "^isc-dhcpv4-relay")
AGENTSERVICESV6=$(pebble services | grep -c "^dhcp6relay")
if [ $AGENTSERVICESV4 -gt 0 ] || [ $AGENTSERVICESV6 -gt 0 ]; then
    # Wait for all interfaces to come up and be assigned IPv4 addresses before
    # starting the DHCP relay agent(s). If an interface the relay should listen
    # on is down, the relay agent will not start. If an interface the relay
    # should listen on is up but does not have an IP address assigned when the
    # relay agent starts, it will not listen or send on that interface for the
    # lifetime of the process.
    /usr/bin/wait_for_intf.sh
fi

pebble start dhcprelayd

python3 /usr/bin/gen_services.py
