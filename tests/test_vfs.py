"""Unit tests for Copy-on-Write Virtual Filesystem (VFS) and Tenant Workspace Manager."""

import pytest
import tempfile
from pathlib import Path
from sandbox.vfs import OverlayFS
from sandbox.tenant import TenantWorkspaceManager, TenantConfig
from tools.files import read_file, write_file, list_files, set_active_overlay


def test_overlay_fs_cow_lifecycle():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        (base / "existing.txt").write_text("Physical Disk Content", encoding="utf-8")

        vfs = OverlayFS(base_dir=base)

        # Read un-modified file from base disk
        assert vfs.read_text("existing.txt") == "Physical Disk Content"

        # Write new file to overlay (staged)
        vfs.write_text("new_staged.txt", "Virtual Staged Content")
        assert vfs.read_text("new_staged.txt") == "Virtual Staged Content"
        assert not (base / "new_staged.txt").exists()  # Not yet on physical disk

        # Check diff
        diff = vfs.get_diff()
        assert "new_staged.txt" in diff["created"]
        assert diff["total_pending"] == 1

        # Delete in overlay
        vfs.delete_file("existing.txt")
        with pytest.raises(FileNotFoundError):
            vfs.read_text("existing.txt")
        assert (base / "existing.txt").exists()  # Still on disk prior to commit

        # Commit overlay to disk
        count = vfs.commit()
        assert count == 2
        assert (base / "new_staged.txt").exists()
        assert (base / "new_staged.txt").read_text() == "Virtual Staged Content"
        assert not (base / "existing.txt").exists()


def test_overlay_fs_rollback():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        vfs = OverlayFS(base_dir=base)

        vfs.write_text("ephemeral.txt", "To be discarded")
        assert vfs.get_diff()["total_pending"] == 1

        discarded = vfs.rollback()
        assert discarded == 1
        assert vfs.get_diff()["total_pending"] == 0
        with pytest.raises(FileNotFoundError):
            vfs.read_text("ephemeral.txt")


def test_tenant_workspace_quotas():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        wm = TenantWorkspaceManager(root_dir=root)
        wm.register_tenant(TenantConfig(
            tenant_id="tenant_a",
            quota_bytes=100,  # 100 bytes limit
            allowed_extensions=[".txt", ".json"],
        ))

        # Allowed write within quota
        wm.validate_write("tenant_a", "doc.txt", "short content")

        # Prohibited extension
        with pytest.raises(PermissionError, match="not allowed"):
            wm.validate_write("tenant_a", "script.sh", "echo hi")

        # Quota exceeded
        with pytest.raises(ValueError, match="exceeds tenant quota"):
            wm.validate_write("tenant_a", "large.txt", "X" * 150)


def test_files_tool_overlay_integration():
    with tempfile.TemporaryDirectory() as tmpdir:
        vfs = OverlayFS(base_dir=Path(tmpdir))
        set_active_overlay(vfs)
        try:
            w_res = write_file("staged.txt", "Staged through tool")
            assert w_res.ok is True
            assert "staged" in w_res.output.lower()

            r_res = read_file("staged.txt")
            assert r_res.ok is True
            assert r_res.output == "Staged through tool"
        finally:
            set_active_overlay(None)
