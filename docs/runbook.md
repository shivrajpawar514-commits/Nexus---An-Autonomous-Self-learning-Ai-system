# Nexus Production Operations Runbook

## Overview
This runbook provides operational guidelines, alerting thresholds, and failure-recovery protocols for deploying and maintaining the Nexus Autonomous Self-Learning AI Agent system in production environments.

---

## 1. Health Checks & Metrics
- **Health Check URL**: `GET /api/health` (returns `{"status": "ok"}`)
- **Prometheus Metrics Scraper**: `GET /metrics`
- **Telemetry Endpoints**: `GET /api/stats`, `GET /api/episodes`

### Key Telemetry Gauges
| Metric | Type | Purpose |
| :--- | :--- | :--- |
| `nexus_tasks_total` | Counter | Cumulative task invocations |
| `nexus_tasks_passed_total` | Counter | Successfully verified executions |
| `nexus_tasks_failed_total` | Counter | Unresolved or failed executions |
| `nexus_token_usage_total` | Counter | Total prompt and completion tokens |
| `nexus_execution_duration_seconds` | Counter | Total runtime seconds consumed |
| `nexus_skills_verified_total` | Gauge | Active promoted Voyager tools |

---

## 2. Emergency Recovery Protocols

### High Verification Failure Rates (>20%)
1. Inspect the most recent failure root-causes via `/api/episodes?status=failed`.
2. Check LLM provider rate limits or latency degradation.
3. Review whether newly promoted skills in `SkillLibrary` introduced regressions.
4. Purge poisoned lessons if needed using SQLite query:
   ```sql
   DELETE FROM semantic_memory WHERE trust_weight < 0.3;
   ```

### Memory Index Performance Degradation
Run vector quantization to compress in-memory indices:
```python
from memory.semantic import SemanticMemory
mem = SemanticMemory()
mem.index.compress_vectors(precision="float16")
```
