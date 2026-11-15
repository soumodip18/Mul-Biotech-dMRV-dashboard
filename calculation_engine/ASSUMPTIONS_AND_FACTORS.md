# Assumptions, Factors and Items Needing Expert Approval

**Engine version:** v0.1.0 (V1, computational foundation)
**Scope:** `calculation_engine/` on branch `calculation-engine-v1`

This document lists every assumption, factor and limit the engine uses, where each one is stored, and which ones still need approval by a person with domain knowledge. Nothing here has been reviewed by an external expert yet.

**What the engine does not claim.** All results are calculated or modelled values, not direct field observations. Every result is saved with the status `QA_PENDING`. The engine does not issue carbon credits and makes no claim of third party verification.

---

## 1. Factors

All factor files are in `calculation_engine/factors/`. The record of each calculation stores the factor ID and version that was used.

| ID | Name | File | Value | Status | Needs approval |
|---|---|---|---|---|---|
| FAC-001 | Carbon to CO2 equivalent | `emission_factors/co2_conversion.json` | 3.666667 (44 / 12) | Physical constant | No, only a check of the number |
| FAC-002 | Carbon fraction of dry tree biomass | `biomass_factors/carbon_fractions.json` | 0.47 | `DRAFT_PENDING_REVIEW` | Yes |
| FAC-003 | Root to shoot ratio | `biomass_factors/root_shoot_ratios.json` | 0.24 | `DRAFT_PENDING_REVIEW` | Yes |
| FAC-004 | Allometric biomass equation EQ-001 | `biomass_factors/allometric_equations.json` | 0.0673 x (wood density x DBH^2 x height)^0.976 | `DRAFT_PENDING_REVIEW` | Yes |
| FAC-005 | Wood density by species | `biomass_factors/wood_density.json` | Empty template | `TEMPLATE_NOT_FILLED` | Yes, values and sources are missing |
| FAC-006 | Unit conversions | `conversion_factors/units.json` | Standard unit ratios | Constant | No |

**Emission factors.** V1 has no emission factors such as fuel or fertiliser. The only emission type factor is the carbon to CO2 conversion (FAC-001).

**How values are used.**
- FAC-001 is read from its file by the soil and tree calculators.
- FAC-003 (root to shoot ratio) is used only when the observation does not supply its own value. The record shows `applied_defaults` and a `DEFAULT_APPLIED` warning when this happens.
- FAC-004 is selected by the equation ID in the observation. The equation is also written as Python code in `calculators/biomass_equations.py` and a test checks that the code matches the stated formula.
- FAC-002 and FAC-005 are not read by the calculators yet. Carbon fraction and wood density are supplied with each observation.

**Sources named in the factor files** (cited by the author and not independently checked yet):
- Equation EQ-001: Chave et al. 2014, Global Change Biology 20(10): 3177 to 3190.
- Carbon fraction 0.47: IPCC 2006 Guidelines, Volume 4, Chapter 4 (default value).
- Root to shoot ratio 0.24: a placeholder based on the IPCC 2006 default range for tropical forests. The exact table value must be confirmed.

---

## 2. Items that need expert approval

These are the values and rules that could change a result. Until they are approved, every affected record carries warnings (`UNAPPROVED_FACTOR`, `DEFAULT_APPLIED`, `NO_STATED_UNCERTAINTY`).

| # | Item | Where | What must be confirmed | Effect if wrong |
|---|---|---|---|---|
| 1 | Biomass equation EQ-001 | FAC-004 | That it suits the project species, region and planting type. It was developed for tropical forest trees | Changes above ground biomass and every result built on it |
| 2 | Root to shoot ratio 0.24 | FAC-003 | Correct value for the species and region, with the exact source table | Changes below ground biomass in direct proportion |
| 3 | Carbon fraction 0.47 | FAC-002 | Whether a species or region value should replace the default | Changes carbon stock and CO2e in direct proportion |
| 4 | Wood density table | FAC-005 | Species list and sourced values (for example from the Global Wood Density Database) | Currently supplied by hand with each observation |
| 5 | Default uncertainty percentage | METH-001, METH-002 | A number for the methodology, or confirmation that results stay without a stated uncertainty | Results show no uncertainty until a value exists |
| 6 | Validation limits | `validation/rules.json` | The sanity limits in section 4 | Valid data may be rejected, or bad data accepted |
| 7 | Methodology status | METH-001, METH-002, METH-003 | Review of formulas, inputs and applicability. All are marked `DRAFT_PENDING_REVIEW` | None of the methodologies are approved |
| 8 | Missing evidence rule | Validator | Whether a missing evidence reference should block a calculation or only warn | Currently only a warning |

---

## 3. Assumptions by methodology

### METH-003: tree survival and biomass monitoring
- Tree counts come from a direct field count of the plot.
- The planted count is the original verified planting record.
- Counts are treated as exact. If a figure comes from a sample, it must be flagged and the sampling method recorded.
- Limitation: it measures survival only, not tree size or growth, and does not separate causes of death.

### METH-002: soil organic carbon
- SOC and bulk density were measured on the same sample and depth layer.
- The sampled layer represents the whole stated area.
- If gravel fraction is not supplied, 0 is used and this is recorded in the calculation record.
- Formula: SOC (%) x bulk density (g/cm3) x depth (cm) x (1 - gravel fraction) gives tonnes of carbon per hectare. This is multiplied by area, then by the CO2 factor.
- Uncertainty: a laboratory value supplied with the observation is carried into the result. Otherwise the result shows no stated uncertainty.
- Limitations: one soil layer only (several layers must be calculated separately and added), no equivalent soil mass correction, and a stock at one point in time, not a change over time.

### METH-001: tree and agroforestry carbon
- DBH and height are plot or species averages for the surviving trees.
- The selected biomass equation is valid for the species and region.
- Wood density, root to shoot ratio and carbon fraction are approved by a methodology reviewer (not yet true, see section 2).
- Surviving trees equal the number of trees multiplied by the survival rate.
- Limitations: using average DBH and height understates biomass in plots with mixed tree sizes. Pantropical equations may not fit every species. Soil, litter and deadwood carbon pools are not included. The result is a stock, not a removal over time.

---

## 4. Validation limits used by the engine

Stored in `calculation_engine/validation/rules.json`. They are sanity limits chosen by the author and are pending review.

| Input | Allowed range |
|---|---|
| trees_planted, num_trees | Whole number greater than 0 |
| trees_surviving | Whole number from 0 up to trees_planted |
| survival_rate | 0 to 100 (%) |
| dbh | Greater than 0 up to 1000 (cm) |
| height | Greater than 0 up to 150 (m) |
| wood_density | 0.1 to 1.5 (g/cm3) |
| plot_area, area | Greater than 0 (ha) |
| carbon_fraction | 0 to 1 |
| root_shoot_ratio | 0 or more |
| soc_percent | 0 to 100 (%) |
| bulk_density | Greater than 0 up to 3 (g/cm3) |
| soil_depth | Greater than 0 up to 300 (cm) |
| gravel_fraction | 0 to 1 |

---

## 5. How the engine behaves, in general

- **Units are not converted automatically.** A value given in a different unit from the one the methodology expects is rejected.
- **Nothing is invented.** If an uncertainty, factor or input is missing, the engine either rejects the observation or records a warning. It never fills the gap silently.
- **Rounding.** Results are rounded to 4 decimal places.
- **The CO2 factor** is stored as 3.666667 while the formula text says 44 / 12 (3.6666667). The difference is far below the rounding and does not change results.
- **Duplicates.** The same observation cannot be calculated twice under the same methodology and engine version. A new methodology or engine version allows a new record, and the old one is kept.
- **Records are never overwritten.** Each calculation creates a new file.
- **Exports** (`calculation_engine/export.py`) read records and never change them. Each export carries a notice that nothing in it is a verified carbon credit.

---

## 6. What to do when an item is approved

1. Update the value, source and status in the factor file, or add `default_uncertainty_percent` and `uncertainty_applies_to` to the methodology file.
2. Increase the version number of the changed file, so old and new results can be told apart.
3. Update the sample expected outputs in `calculation_engine/samples/` on purpose, because results and warnings will change.
4. Run the full test suite (`python -m pytest calculation_engine/tests -v`).
5. Record the change and the approver in `HANDOVER.md`.
