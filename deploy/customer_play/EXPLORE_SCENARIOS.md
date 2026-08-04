# Explore scenarios — HVAC CFD airflow

## Prompts

```text
Run steady RANS k-ω SST on the multi-branch HVAC duct network and report pressure drop and diffuser uniformity
Optimize airflow with damper adjustments to reduce pressure drop and improve thermal comfort
```

## Understanding results

| Field | Meaning |
|-------|---------|
| `ok: true` | Pipeline ran |
| `passed: false` | Metrics missed `max_delta_p_Pa` / `min_uniformity` |
| `delta_p_Pa` | System pressure drop |
| `uniformity_index` | Diffuser velocity uniformity |
| `damper_fractions` | After optimize path |

Default targets: ΔP ≤ 150 Pa, uniformity ≥ 0.75. Baseline stub ΔP is often slightly over 150 so first run can show **passed=false**.
