---
name: hvac_cfd
trigger: airflow, HVAC, duct, diffuser, pressure drop, RANS, damper, k-omega, turbulence, thermal comfort, uniformity
tags: cfd, hvac, airflow
---

# HVAC duct network — steady RANS CFD

Use this bundle when the user wants to **simulate or optimize airflow** in a
multi-branch commercial HVAC duct system (diffusers, bends, dampers).

## Preferred pipelines

- **hvac_airflow_pipeline** — build case → steady RANS (k-ω SST) → evaluate metrics
- **hvac_optimize_dampers_pipeline** — CFD → damper proposal → re-solve → evaluate

## Physics defaults

- Steady-state RANS
- Turbulence model: **k-ω SST**
- Inlet: mass flow
- Outlet: static pressure

## Metrics

- Branch pressure drop (ΔP)
- Diffuser velocity uniformity index
- Turbulence intensity near bends
- Pass if ΔP and uniformity meet targets
