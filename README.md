# 🐕 DINGO Mesh & Autonomous Edge Cluster Test Repository

[![Jules Session Ready](https://img.shields.io/badge/Google%20Jules-24%2F7%20Sentinel%20Active-brightgreen)](https://jules.google.com/session)

This repository serves as the central continuous integration, regression testing, and autonomous maintenance bridge for the **DINGO Autonomous Edge Cluster** (`van01`, `van02`, `brain01`, `node01`, `server01`, `omada-gw`).

---

## 1. Directory Structure

```text
dingo-mesh-test/
├── ci/
│   └── integrity-audit.yml          # 24/7 CI workflow definition & regression guard
├── .jules/
│   └── instructions.md              # Jules operational instructions & quota-safe guidelines
├── config/
│   ├── devices.json                 # Single Source of Truth for cluster node metadata & IPs
│   └── NODE_PROVISIONING_SPEC.md    # Automated 6-phase node onboarding specification
├── scripts/
│   └── hub-terminal-dispatch.sh     # Web Terminal Fabric shell dispatcher script
├── tests/
│   └── test_cluster_integrity.py    # Automated regression test suite
├── dingo-cluster-test.json          # Cluster node topography manifest
├── JULES.md                         # Jules background engineer manual & reference roster
└── README.md
```

---

## 2. Jules 24/7 Autonomous Sentinel Architecture

To keep Google Jules operating **24/7** without exhausting token quotas or exceeding plan allowances, DINGO implements a **Tiered Watchdog**:

1. **Tier 1: Zero-Token CI Sentinel**:
   - Runs deterministic static checks against the codebase (`python -m unittest tests/test_cluster_integrity.py`).
   - Cross-validates all dispatcher scripts, SSH target connection strings, and network bounds against `config/devices.json`.
   - Cost: **0 Jules tokens** (consumes free CI compute).

2. **Tier 2: Targeted Event-Driven Jules Remediation**:
   - If any configuration drift, broken SSH connection string, or schema discrepancy occurs, Jules references [`JULES.md`](JULES.md) to locate the exact fix.
   - Because `JULES.md` provides high-density context (node IPs, user accounts, and test commands), Jules completes the repair in **1 single shot** rather than burning multi-turn inference cycles.

3. **Tier 3: Continuous PR & Code Quality Sentinel**:
   - Jules reviews open PRs, prevents performance regressions on `node01` during active 3D printing, and keeps documentation synchronized with cluster state.

---

## 3. Running Integrity Tests Locally

```bash
python -m unittest tests/test_cluster_integrity.py -v
```
