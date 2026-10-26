#!/usr/bin/env bash
# ==============================================================================
# Circle of Trust: Hub Web Terminal Dispatcher (ttyd backend)
# Dispatches terminal sessions strictly under the unified 'dingo' service account:
#   ?arg=van01     -> Local Pi 5 Primary Edge Node (dingo)
#   ?arg=van02     -> Pi 5 Secondary Edge / Workstation Node (dingo@192.168.0.105)
#   ?arg=brain01   -> Windows 11 Neural Workstation Node (dingo@192.168.0.108)
#   ?arg=node01    -> Fabrication Node / Klipper Pi 4B (dingo@192.168.0.107)
#   ?arg=server01  -> Cloud Anchor / GCP us-central1 (dingo@192.168.219.1)
#   ?arg=omada-gw  -> TP-Link Omada ER706W Hardware Gateway (gw-cli)
# ==============================================================================
set -e

TARGET="${1:-van01}"
LOCAL_HOST=$(hostname 2>/dev/null || echo "van01")

clear

case "$TARGET" in
  van01)
    if [[ "$LOCAL_HOST" == *"van01"* ]]; then
      echo -e "\033[1;36m========================================================================\033[0m"
      echo -e "\033[1;32m ✔ Connected to van01 (Primary Edge Gateway / Active Host Controller)\033[0m"
      echo -e "\033[2m Host: 192.168.0.106 | User: dingo | Circle of Trust\033[0m"
      echo -e "\033[1;36m========================================================================\033[0m\n"
      cd /home/dingo 2>/dev/null || cd /home/admin
      exec sudo -u dingo -i
    else
      echo -e "\033[1;33mConnecting to van01 (192.168.0.106) via SSH as dingo...\033[0m"
      exec ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 dingo@192.168.0.106
    fi
    ;;

  van02)
    if [[ "$LOCAL_HOST" == *"van02"* ]]; then
      echo -e "\033[1;36m========================================================================\033[0m"
      echo -e "\033[1;33m ✔ Connected to van02 (Secondary Edge Node / Pi 5 Replica Host)\033[0m"
      echo -e "\033[2m Host: 192.168.0.105 | User: dingo | Circle of Trust\033[0m"
      echo -e "\033[1;36m========================================================================\033[0m\n"
      cd /home/dingo 2>/dev/null || cd /home/admin
      exec sudo -u dingo -i
    else
      echo -e "\033[1;33mConnecting to van02 (192.168.0.105) via SSH as dingo...\033[0m"
      exec ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 dingo@192.168.0.105
    fi
    ;;

  brain01)
    echo -e "\033[1;36m========================================================================\033[0m"
    echo -e "\033[1;35m 🧠 Connecting to brain01 (Neural Compute Node • Windows 11 / WSL2)\033[0m"
    echo -e "\033[2m Host: 192.168.0.108 | User: dingo | Circle of Trust\033[0m"
    echo -e "\033[1;36m========================================================================\033[0m\n"
    if ! ping -c 1 -W 2 192.168.0.108 >/dev/null 2>&1; then
      echo -e "\033[1;31m[-] Host 192.168.0.108 (brain01) is currently unreachable or sleeping.\033[0m"
      echo -e "\033[2mTip: You can send a Wake-on-LAN magic packet from the dashboard\033[0m\n"
      echo "Attempting SSH connection anyway (Press Ctrl+C to abort)..."
    fi
    exec ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 dingo@192.168.0.108 || {
      echo -e "\n\033[1;31mConnection closed.\033[0m Press Enter to return to local shell."
      read -r
      exec /bin/bash -i
    }
    ;;

  node01)
    echo -e "\033[1;36m========================================================================\033[0m"
    echo -e "\033[1;33m 🖨️ Connecting to node01 (Fabrication Node • Klipper / Mainsail Pi 4B)\033[0m"
    echo -e "\033[2m Host: 192.168.0.107 | User: dingo | Circle of Trust\033[0m"
    echo -e "\033[1;36m========================================================================\033[0m\n"
    exec ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 dingo@192.168.0.107 || {
      echo -e "\n\033[1;31mConnection closed.\033[0m Press Enter to return to local shell."
      read -r
      exec /bin/bash -i
    }
    ;;

  server01)
    echo -e "\033[1;36m========================================================================\033[0m"
    echo -e "\033[1;34m ☁️ Connecting to server01 (Cloud Anchor • Debian 12 / GCP us-central1)\033[0m"
    echo -e "\033[2m VPN Host: 192.168.219.1 | User: dingo | Circle of Trust\033[0m"
    echo -e "\033[1;36m========================================================================\033[0m\n"
    exec sudo -u dingo ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 dingo@192.168.219.1 || {
      echo -e "\n\033[1;31mConnection closed.\033[0m Press Enter to return to local shell."
      read -r
      exec /bin/bash -i
    }
    ;;

  omada-gw|router|er706w)
    echo -e "\033[1;36m========================================================================\033[0m"
    echo -e "\033[1;36m 🌐 TP-Link Omada ER706W Gateway (Wi-Fi 6 AX3000 • Standalone LuCI)\033[0m"
    echo -e "\033[2m Perimeter Gateway: 192.168.0.1 | Dropbear SSH Port 22 | LuCI HTTPS Port 443\033[0m"
    echo -e "\033[1;36m========================================================================\033[0m\n"
    exec /usr/local/bin/gw-cli interactive
    ;;

  *)
    echo -e "\033[1;31mUnknown target device: ${TARGET}\033[0m"
    echo "Falling back to local dingo shell..."
    exec sudo -u dingo -i
    ;;
esac
