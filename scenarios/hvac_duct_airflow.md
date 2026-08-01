# Scenario — CFD: HVAC System Airflow Optimization

## Objective

Optimize airflow distribution in a commercial building HVAC duct system to reduce pressure drop and improve thermal comfort.

## Description

Simulate airflow through a multi-branch duct network with diffusers, bends, and dampers. Evaluate:

- Pressure drop across each branch
- Velocity uniformity at diffusers
- Turbulence intensity near bends
- Effectiveness of damper adjustments

## CAE methods

- Steady-state RANS CFD
- Turbulence model: k-ω SST
- Boundary conditions: inlet mass flow, outlet static pressure
- Outputs: velocity contours, pressure maps, flow uniformity index

## App mapping

| Need | Skill / pipeline |
|------|------------------|
| Case + BC | `build_duct_case` |
| RANS solve | `run_rans_cfd` |
| Metrics | `evaluate_hvac_metrics` |
| Damper proposal | `adjust_dampers` |
| Full study | `hvac_airflow_pipeline` |
| Optimize distribution | `hvac_optimize_dampers_pipeline` |

## Example prompts

```text
Run steady RANS k-ω SST on the multi-branch HVAC ducts and report pressure drop and uniformity.

Optimize airflow with damper adjustments to reduce pressure drop and improve thermal comfort.
```
