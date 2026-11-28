# ADR 005: Copy-on-Write Virtual Filesystem (VFS) & Multi-Tenant Workspace Isolation

## Status
Accepted

## Context
When autonomous agents execute complex or multi-agent workflows concurrently, direct writes to physical disk present multiple risks:
1. File collisions across concurrent subagents or tenant requests.
2. Unrecoverable side effects when a task fails verification mid-way.
3. Disk resource exhaustion without per-tenant storage quotas.

## Decision
We implement:
1. **Copy-on-Write Virtual Filesystem (`OverlayFS`)**:
   - In-memory virtual overlay intercepting all reads, writes, and deletions.
   - Reads fall through to physical base directory only for untouched files.
   - Explicit two-phase commit: changes can be cleanly committed (`commit()`) or rolled back (`rollback()`).
2. **Tenant Workspace Manager (`TenantWorkspaceManager`)**:
   - Enforces per-tenant directory isolation, byte quotas, and file extension whitelists.
3. **Tool Integration**:
   - `tools/files.py` supports session-scoped overlays without breaking backwards compatibility.
4. **Observability & Management**:
   - Exposed via `/api/vfs/status` and `/api/vfs/commit` on dashboard server.

## Consequences
- Guaranteed zero-pollution execution for failed or speculative agent trajectories.
- Complete thread-safe tenant isolation.
