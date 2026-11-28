"""Copy-on-Write (CoW) Virtual Filesystem Overlay for isolated agent execution."""

from __future__ import annotations
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class VirtualFile(BaseModel):
    path: str
    content: str
    is_deleted: bool = False
    modified_at: float = Field(default_factory=time.time)


class OverlayFS:
    """Provides a thread-safe Copy-on-Write virtual layer on top of a physical base directory."""

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._overlay: Dict[str, VirtualFile] = {}

    def _normalize_rel_path(self, rel_path: str) -> str:
        p = Path(rel_path)
        norm = os.path.normpath(str(p)).lstrip("/")
        if norm.startswith("..") or "/../" in norm:
            raise PermissionError(f"Access denied: Path '{rel_path}' escapes sandbox boundary.")
        return norm

    def read_text(self, rel_path: str) -> str:
        norm = self._normalize_rel_path(rel_path)
        if norm in self._overlay:
            vf = self._overlay[norm]
            if vf.is_deleted:
                raise FileNotFoundError(f"File not found (deleted in overlay): {rel_path}")
            return vf.content

        # Fallback to physical disk
        physical_path = (self.base_dir / norm).resolve()
        if not str(physical_path).startswith(str(self.base_dir)):
            raise PermissionError(f"Access denied: Path '{rel_path}' escapes sandbox boundary.")
        if not physical_path.exists() or not physical_path.is_file():
            raise FileNotFoundError(f"File not found on disk: {rel_path}")

        return physical_path.read_text(encoding="utf-8")

    def write_text(self, rel_path: str, content: str) -> None:
        norm = self._normalize_rel_path(rel_path)
        self._overlay[norm] = VirtualFile(path=norm, content=content, is_deleted=False)

    def delete_file(self, rel_path: str) -> None:
        norm = self._normalize_rel_path(rel_path)
        self._overlay[norm] = VirtualFile(path=norm, content="", is_deleted=True)

    def list_dir(self, rel_dir: str = "") -> List[str]:
        norm_dir = self._normalize_rel_path(rel_dir) if rel_dir else ""
        physical_dir = (self.base_dir / norm_dir).resolve()

        items = set()
        if physical_dir.exists() and physical_dir.is_dir():
            for p in physical_dir.iterdir():
                items.add(p.name)

        # Merge overlay changes
        for path_str, vf in self._overlay.items():
            parent_dir = str(Path(path_str).parent)
            if parent_dir == "." or parent_dir == "":
                parent_dir = ""
            if parent_dir == norm_dir:
                if vf.is_deleted:
                    items.discard(Path(path_str).name)
                else:
                    items.add(Path(path_str).name)

        return sorted(list(items))

    def commit(self) -> int:
        """Write all staged overlay changes to physical disk and flush overlay."""
        count = 0
        for norm, vf in self._overlay.items():
            target = (self.base_dir / norm).resolve()
            if vf.is_deleted:
                if target.exists():
                    target.unlink()
                    count += 1
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(vf.content, encoding="utf-8")
                count += 1
        self._overlay.clear()
        return count

    def rollback(self) -> int:
        """Discard all staged overlay changes without affecting physical disk."""
        count = len(self._overlay)
        self._overlay.clear()
        return count

    def get_diff(self) -> Dict[str, Any]:
        """Summarize staged changes in the overlay."""
        created = []
        modified = []
        deleted = []

        for norm, vf in self._overlay.items():
            if vf.is_deleted:
                deleted.append(norm)
            else:
                physical_path = (self.base_dir / norm).resolve()
                if physical_path.exists():
                    modified.append(norm)
                else:
                    created.append(norm)

        return {
            "created": created,
            "modified": modified,
            "deleted": deleted,
            "total_pending": len(self._overlay),
        }
