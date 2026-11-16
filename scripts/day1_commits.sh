#!/usr/bin/env bash
set -e

REPO_URL="https://github.com/shivrajpawar514-commits/Nexus---An-Autonomous-Self-learning-Ai-system.git"

echo "========================================================"
echo "  EXECUTING DAY 1 COMMITS (3 COMMITS CADENCE)"
echo "========================================================"

# Configure remote origin if not set
if ! git remote get-url origin >/dev/null 2>&1; then
    echo "[+] Configuring remote origin: $REPO_URL"
    git remote add origin "$REPO_URL"
else
    echo "[+] Remote origin already configured: $(git remote get-url origin)"
fi

git branch -M main

# --- COMMIT 1: Project Structure & Core Dependencies ---
echo ""
echo "[+] Creating Commit 1 of 3: Project Structure & Core Dependencies..."
git add requirements.txt Makefile .gitignore
git commit -m "chore: initialize nexus project structure and core dependencies

- Add pinned dependencies for FastAPI, Pytest, Pydantic, and Ollama
- Define Makefile automation targets for install, test, eval, and dashboard
- Configure gitignore rules for Python bytecode, virtualenv, and SQLite databases" || echo "Already committed."

# --- COMMIT 2: Tool Registry & Permission Tiers ---
echo ""
echo "[+] Creating Commit 2 of 3: Environment Configuration & Permission Tiers..."
git add tools/base.py tools/__init__.py
git commit -m "feat(config): implement environment configuration and permission tiers

- Implement ToolRegistry with dynamic runtime tool registration
- Define PermissionTier enum (READ_ONLY, CONFIRMATION_REQUIRED, RESTRICTED)
- Add Pydantic ToolResult validation with JSON serialization" || echo "Already committed."

# --- COMMIT 3: Architecture & Security Documentation ---
echo ""
echo "[+] Creating Commit 3 of 3: Architectural Design Specification..."
git add README.md docs/design.md docs/safety.md docs/research_notes.md
git commit -m "docs: author architectural design specification and threat model

- Document end-to-end Plan-Act-Observe-Verify-Reflect-Store architecture
- Detail deterministic AST sandboxing threat model and path jail restrictions
- Summarize research literature on ReAct, Reflexion, Voyager, and MemGPT" || echo "Already committed."

echo ""
echo "========================================================"
echo "  DAY 1 COMMITS COMPLETED SUCCESSFULLY!"
echo "========================================================"
echo "Run 'git log -n 3 --oneline' to view your commits."
echo "Run 'git push -u origin main' to publish to GitHub."

