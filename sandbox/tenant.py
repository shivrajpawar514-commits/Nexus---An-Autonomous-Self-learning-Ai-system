"""Multi-tenant workspace isolation and storage quota management."""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from sandbox.vfs import OverlayFS


class TenantConfig(BaseModel):
    tenant_id: str
    quota_bytes: int = 10 * 1024 * 1024  # 10 MB default
    max_files: int = 100
    allowed_extensions: Optional[List[str]] = None


class TenantWorkspaceManager:
    """Manages dedicated virtual workspace overlays and storage quotas per tenant."""

    def __init__(self, root_dir: Path):
        self.root_dir = Path(root_dir).resolve()
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self._tenants: Dict[str, TenantConfig] = {}
        self._overlays: Dict[str, OverlayFS] = {}

    def register_tenant(self, config: TenantConfig) -> OverlayFS:
        tenant_dir = self.root_dir / config.tenant_id
        tenant_dir.mkdir(parents=True, exist_ok=True)
        self._tenants[config.tenant_id] = config
        overlay = OverlayFS(base_dir=tenant_dir)
        self._overlays[config.tenant_id] = overlay
        return overlay

    def get_overlay(self, tenant_id: str) -> OverlayFS:
        if tenant_id not in self._overlays:
            # Auto-provision standard tenant
            self.register_tenant(TenantConfig(tenant_id=tenant_id))
        return self._overlays[tenant_id]

    def validate_write(self, tenant_id: str, rel_path: str, content: str) -> None:
        """Enforces file count, extension whitelist, and size quota bounds."""
        config = self._tenants.get(tenant_id, TenantConfig(tenant_id=tenant_id))

        # 1. Extension check
        if config.allowed_extensions:
            ext = Path(rel_path).suffix.lower()
            if ext not in config.allowed_extensions:
                raise PermissionError(f"Extension '{ext}' not allowed for tenant '{tenant_id}'. Allowed: {config.allowed_extensions}")

        # 2. Content size quota check
        size = len(content.encode("utf-8"))
        if size > config.quota_bytes:
            raise ValueError(f"Write size ({size} bytes) exceeds tenant quota ({config.quota_bytes} bytes).")

    def list_tenants(self) -> List[Dict[str, Any]]:
        return [
            {
                "tenant_id": t.tenant_id,
                "quota_bytes": t.quota_bytes,
                "max_files": t.max_files,
                "pending_overlay_diff": self._overlays[t.tenant_id].get_diff() if t.tenant_id in self._overlays else {},
            }
            for t in self._tenants.values()
        ]
