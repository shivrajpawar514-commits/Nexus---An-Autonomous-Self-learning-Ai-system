---
name: ui-ux-pro-max
description: Professional UI/UX engineering guidelines for high-utility, accessible, and high-density developer consoles and dashboards.
---

# UI/UX Pro Max Guidelines

## Core Principles
1. **Utility-First Information Architecture**:
   - Prioritize high signal-to-noise ratio over decorative fluff.
   - Every pixel must serve an operational purpose: metrics, statuses, execution steps, logs, or controls.
   - Standard 4px / 8px grid alignment with strict padding and margin rhythm.

2. **Typography Hierarchy**:
   - Monospace font (`JetBrains Mono`, `SF Mono`, `ui-monospace`) for numerical data, IDs, hashes, timestamps, and code artifacts.
   - Clean sans-serif (`Inter`, `system-ui`, `-apple-system`) for structural labels and readable explanations.
   - Strict size scale: `text-[10px]` for metadata, `text-[11px]` for badges, `text-xs` (12px) for table/card copy, `text-sm` (14px) for card headers, `text-base`/`text-lg` for primary KPIs.

3. **Color & Contrast Accessibility**:
   - True neutral dark backgrounds (`#09090b` zinc-950, `#18181b` zinc-900, `#27272a` zinc-800).
   - High WCAG AAA compliant text contrast (primary `#f4f4f5`, secondary `#a1a1aa`, muted `#71717a`).
   - Semantically reserved accent colors:
     - Emerald (`#16a34a` / `#4ade80`): Passed, Verified, Healthy.
     - Rose (`#dc2626` / `#f87171`): Failed, Intercepted, Critical Error.
     - Blue (`#2563eb` / `#60a5fa`): Primary Action, Active Navigation, Info.
     - Amber (`#d97706` / `#fbbf24`): Pending, Warning, In-Progress.
   - No decorative purple gradients, drop shadows with high opacity, or visual vibration.

4. **Interactive State Feedback**:
   - Clear hover, active, focus-visible, and disabled states on all interactive controls.
   - Immediate feedback upon action dispatch (e.g., spinning icon, disabled state during async operations).

