---
name: stitch-mcp
description: Guidelines and MCP component integration patterns for stitching atomic UI blocks into modular dashboards and developer consoles.
---

# Stitch MCP Component Architecture

## Core Architectural Workflow
1. **Atomic Component Decomposition**:
   - Deconstruct complex layouts into standalone, reusable modules:
     - Header / Navigation Bar
     - KPI Stat Tile (Metric + Delta + Provenance)
     - Control Panel (Inputs + Filters + Toggles + CTA)
     - Live Stepper / Execution Feed (Step + State + Content)
     - Telemetry Table (Pagination + Filter + Row Details)
     - Inspection Drawer / Modal

2. **Declarative Component Interfaces**:
   - Each stitched module must accept structured JSON payloads directly from backend REST endpoints without manual DOM re-parsing.
   - Maintain a single source of truth for UI state (e.g., active tab, selected episode ID, filter status).

3. **Stateless UI Assembly**:
   - Components should render idempotently based on incoming API data.
   - Use structured event delegation for click handlers (`onclick="viewEpisodeModal(id)"`) to avoid memory leaks.

