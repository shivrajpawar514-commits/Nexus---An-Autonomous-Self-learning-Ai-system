# Enterprise Security Policy & RBAC Specification

## Overview
Nexus enforces a zero-trust execution model. Every autonomous tool execution, subagent invocation, and human-in-the-loop task is audited against a dual-layer security boundary:
1. **Role-Based Access Control (RBAC)** governing tenant role hierarchy (`ADMIN > OPERATOR > RESEARCHER > READONLY`).
2. **Declarative Action Policy Engine** with explicit DENY overrides, wildcard pattern matching, and parameter regex validation.

## Policy Schema
```json
{
  "id": "block_sensitive_files",
  "name": "Block Root Path Modifications",
  "effect": "DENY",
  "actions": ["files:*", "write_file", "delete_file"],
  "resources": ["/etc/*", "/sys/*", "/root/*"],
  "conditions": {
    "filename": ".*(\\.pem|\\.key|id_rsa)$"
  }
}
```

## RBAC Role Hierarchy
| Role | Privilege Tier | Allowed Capabilities |
|---|---|---|
| `ADMIN` | 400 | Full system reconfiguration, policy modifications, sandbox override |
| `OPERATOR` | 300 | Autonomous tool execution, task queue submission, subagent spawning |
| `RESEARCHER` | 200 | Benchmark evaluations, read-only memory queries, dataset exploration |
| `READONLY` | 100 | Telemetry viewing, dashboard inspection, read-only calculator/file access |
