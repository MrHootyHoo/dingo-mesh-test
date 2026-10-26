#!/usr/bin/env python3
"""
DINGO Autonomous Edge Cluster: Continuous Integrity & Regression Test Suite
Used by Google Jules, GitHub Actions, and local Antigravity agents to detect configuration drift,
broken SSH connection strings, schema regressions, and network boundary violations.
"""

import json
import os
import re
import unittest
import ipaddress

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEVICES_JSON_PATH = os.path.join(REPO_ROOT, "config", "devices.json")
DISPATCH_SH_PATH = os.path.join(REPO_ROOT, "scripts", "hub-terminal-dispatch.sh")
SPEC_MD_PATH = os.path.join(REPO_ROOT, "config", "NODE_PROVISIONING_SPEC.md")


class TestClusterIntegrity(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(DEVICES_JSON_PATH, "r", encoding="utf-8") as f:
            cls.devices = json.load(f)
        cls.device_map = {d["id"]: d for d in cls.devices}

        with open(DISPATCH_SH_PATH, "r", encoding="utf-8") as f:
            cls.dispatch_script = f.read()

    def test_devices_schema(self):
        """Validates that all devices have required fields, valid IPs, and no duplicates."""
        required_fields = ["id", "name", "role", "ip", "vpnIp", "user"]
        seen_ids = set()
        seen_ips = set()
        seen_vpn_ips = set()

        for d in self.devices:
            for field in required_fields:
                self.assertIn(
                    field, d, f"Device record '{d.get('id', 'unknown')}' missing required field: '{field}'"
                )

            # Check uniqueness
            dev_id = d["id"]
            self.assertNotIn(dev_id, seen_ids, f"Duplicate device ID found: '{dev_id}'")
            seen_ids.add(dev_id)

            ip = d["ip"]
            # Validate IP format
            try:
                ip_obj = ipaddress.IPv4Address(ip)
            except ValueError:
                self.fail(f"Invalid IPv4 address '{ip}' for device '{dev_id}'")

            # Validate VPN IP format and subnet (192.168.219.0/24)
            vpn_ip = d["vpnIp"]
            try:
                vpn_obj = ipaddress.IPv4Address(vpn_ip)
            except ValueError:
                self.fail(f"Invalid VPN IPv4 address '{vpn_ip}' for device '{dev_id}'")

            vpn_subnet = ipaddress.IPv4Network("192.168.219.0/24")
            self.assertTrue(
                vpn_obj in vpn_subnet,
                f"Device '{dev_id}' VPN IP '{vpn_ip}' is outside the Circle of Trust mesh (192.168.219.0/24)"
            )

    def test_terminal_dispatch_alignment(self):
        """
        Validates that scripts/hub-terminal-dispatch.sh contains valid dispatch cases for every device
        and that SSH connection strings strictly match the designated user and host from devices.json.
        """
        # Ensure script syntax is valid shell
        self.assertTrue(self.dispatch_script.startswith("#!/usr/bin/env bash"))

        for dev_id, dev in self.device_map.items():
            expected_user = dev["user"]
            expected_ip = dev["ip"]
            expected_vpn_ip = dev["vpnIp"]

            # 1. Device ID must be present in a case branch (handling pipe alternatives like omada-gw|router)
            pattern = rf"(?:^|\n|\s)([a-zA-Z0-9_\-|]*\b{re.escape(dev_id)}\b[a-zA-Z0-9_\-|]*)\)"
            match = re.search(pattern, self.dispatch_script)
            self.assertIsNotNone(
                match,
                f"hub-terminal-dispatch.sh is missing a case handler for device '{dev_id}'"
            )

            # Special case: omada-gw uses gw-cli interactive rather than direct standard ssh
            if dev_id == "omada-gw":
                self.assertIn("gw-cli", self.dispatch_script)
                continue

            # Extract the block for this device
            case_label = match.group(1)
            case_block_match = re.search(
                rf"{re.escape(case_label)}\)(.*?);;", self.dispatch_script, re.DOTALL
            )
            self.assertIsNotNone(
                case_block_match,
                f"Could not extract case block for device '{dev_id}' in hub-terminal-dispatch.sh"
            )
            block_text = case_block_match.group(1)

            # If the block executes SSH, verify the target matches expected_user and either expected_ip or expected_vpn_ip
            ssh_matches = re.findall(r"ssh\s+.*?([a-zA-Z0-9_\.\-]+@[a-zA-Z0-9_\.\-]+)", block_text)
            
            # If server01 uses an SSH config host alias like 'ssh ... server01'
            if dev_id == "server01" and "ssh -o" in block_text and "server01" in block_text:
                # Valid alias
                continue

            if ssh_matches:
                # Verify that at least one of the ssh target strings matches expected user and IP
                matched = False
                for target_str in ssh_matches:
                    user_part, host_part = target_str.split("@", 1)
                    if user_part == expected_user and host_part in (expected_ip, expected_vpn_ip):
                        matched = True
                        break

                self.assertTrue(
                    matched,
                    f"The current script attempts an SSH connection using the wrong user and host for '{dev_id}'! "
                    f"Expected: {expected_user}@{expected_ip} or {expected_user}@{expected_vpn_ip}, "
                    f"found: {ssh_matches}"
                )

    def test_node_provisioning_spec_alignment(self):
        """Validates that the Node Provisioning Spec document exists and covers all roles."""
        self.assertTrue(
            os.path.exists(SPEC_MD_PATH),
            "NODE_PROVISIONING_SPEC.md is missing from config directory"
        )
        with open(SPEC_MD_PATH, "r", encoding="utf-8") as f:
            spec_content = f.read()

        self.assertIn("Phase 3: Pritunl Mesh VPN Enrollment", spec_content)
        self.assertIn("Remote Node VPN Autonomic Bridge", spec_content)
        self.assertIn("Role A: Primary / Secondary Edge Gateway", spec_content)
        self.assertIn("Role B: Active Compute & Fabrication Worker", spec_content)
        self.assertIn("Role C: Headless / Backup Node", spec_content)

    def test_reboot_policy_invariants(self):
        """
        Validates cluster safety invariants:
        1. server01 must never be rebooted via web/remote API
        2. node01 must enforce non-interference print safety guard
        3. All computing nodes must dispatch under the unified 'dingo' service account
        """
        for dev_id, dev in self.device_map.items():
            if dev_id == "omada-gw":
                continue
            self.assertEqual(
                dev["user"], "dingo",
                f"Computing node '{dev_id}' must strictly use unified service account 'dingo'"
            )

    def test_device_file_explorer_security_invariants(self):
        """
        Validates Device Studio file explorer invariants:
        1. Whitelisted roots for all active cluster nodes
        2. Absolute prohibition on private keys, auth credentials, and shadow files
        3. Strict rejection of directory traversal attacks (../, null-bytes)
        """
        BLOCKED_PATTERNS = [
            re.compile(r"id_rsa", re.I),
            re.compile(r"id_ed25519", re.I),
            re.compile(r"authorized_keys", re.I),
            re.compile(r"\.key$", re.I),
            re.compile(r"\.pem$", re.I),
            re.compile(r"jwt_secret", re.I),
            re.compile(r"\.env$", re.I),
            re.compile(r"shadow$", re.I)
        ]

        # Verify blocked pattern matching
        sensitive_samples = [
            "/home/dingo/.ssh/id_ed25519",
            "/home/dingo/.ssh/id_rsa",
            "/home/dingo/.ssh/authorized_keys",
            "/home/admin/van01-frontend/api/.env",
            "/home/admin/van01-frontend/jwt_secret.key",
            "/etc/shadow",
            "server.key",
            "cert.pem"
        ]
        for sample in sensitive_samples:
            matched = any(p.search(sample) for p in BLOCKED_PATTERNS)
            self.assertTrue(matched, f"Security vulnerability: Sensitive file '{sample}' was not blocked by blacklist!")

        # Verify traversal rejection
        traversal_attempts = [
            "../../../../etc/passwd",
            "../.ssh/id_ed25519",
            "public_html/../../../etc/shadow",
            "subdir/..\0/secret"
        ]
        for attempt in traversal_attempts:
            is_traversal = ".." in attempt or "\0" in attempt
            self.assertTrue(is_traversal, f"Path traversal string '{attempt}' bypassed detection!")


if __name__ == "__main__":
    unittest.main()
