#!/usr/bin/env bash
# ==============================================================================
# DINGO Ephemeral Gateway Node Auto-Registration & Telemetry Reporter
# Dispatches instance metadata to server01 and van01/van02 on boot
# ==============================================================================
set -e

# Gather VM Identity & Cloud Metadata
HOSTNAME=$(hostname)
PUBLIC_IPV4=$(curl -4s --connect-timeout 3 http://ipecho.net/plain 2>/dev/null || curl -4s --connect-timeout 3 https://api.ipify.org 2>/dev/null || echo "34.50.171.148")
INTERNAL_IPV4=$(curl -s -H 'Metadata-Flavor: Google' --connect-timeout 2 http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/ip 2>/dev/null || hostname -I | awk '{print $1}')
ZONE=$(curl -s -H 'Metadata-Flavor: Google' --connect-timeout 2 http://metadata.google.internal/computeMetadata/v1/instance/zone 2>/dev/null | awk -F/ '{print $NF}')
if [ -z "$ZONE" ]; then
  ZONE="us-west4-a"
fi

# Detect tun0 VPN Server Binding
TUN_IP=$(ip -4 addr show tun0 2>/dev/null | grep -oP '(?<=inet\s)\d+(\.\d+){3}' || echo "192.168.235.1")

# Format concise display name
DISPLAY_NAME="${ZONE}-gw...${HOSTNAME: -2}"

echo "[DINGO] Ephemeral Gateway Node Announcing: $HOSTNAME ($DISPLAY_NAME)"
echo "[DINGO] Public IPv4: $PUBLIC_IPV4 | Internal: $INTERNAL_IPV4 | VPN tun0: $TUN_IP"

# Build JSON Announcement Payload
PAYLOAD=$(cat <<EOF
{
  "id": "$HOSTNAME",
  "name": "$DISPLAY_NAME",
  "fullName": "$HOSTNAME",
  "role": "Dynamic Gateway Node (Las Vegas, NV)",
  "type": "Ephemeral Cloud Gateway (GCP e2-micro)",
  "ip": "$PUBLIC_IPV4",
  "internalIp": "$INTERNAL_IPV4",
  "publicIp": "$PUBLIC_IPV4",
  "vpnIp": "$TUN_IP",
  "zone": "$ZONE",
  "port": 16572,
  "status": "online",
  "isGatewayServer": true
}
EOF
)

# Broadcast to cluster hubs (Primary: Cloud Relay on 10.129.0.2:5150 over internal VPC)
HUBS=(
  "http://10.129.0.2:5150"
  "https://websight.website"
  "http://192.168.219.1:5150"
)

for HUB in "${HUBS[@]}"; do
  echo "[DINGO] Registering with Hub at $HUB..."
  curl -s -k -m 4 -X POST \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD" \
    "$HUB/api/gateway-node/announce" >/dev/null 2>&1 || true
done

echo "[DINGO] Gateway announcement sequence completed."
