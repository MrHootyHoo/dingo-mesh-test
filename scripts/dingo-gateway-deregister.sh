#!/usr/bin/env bash
# ==============================================================================
# DINGO Ephemeral Gateway Node Deregistration
# Notifies server01 and van01/van02 on VM shutdown
# ==============================================================================
HOSTNAME=$(hostname)

PAYLOAD=$(cat <<EOF
{
  "id": "$HOSTNAME"
}
EOF
)

HUBS=(
  "http://10.129.0.2:5150"
  "https://websight.website"
  "http://192.168.219.1:5150"
)

for HUB in "${HUBS[@]}"; do
  curl -s -k -m 3 -X POST \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD" \
    "$HUB/api/gateway-node/deregister" >/dev/null 2>&1 || true
done
