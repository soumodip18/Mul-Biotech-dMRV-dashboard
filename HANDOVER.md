# Handover: Mul Biotech dMRV Calculation Engine and Dashboard

**Branch:** `calculation-engine-v1`
**Last updated:** 2026-11-01
**Prepared by:** Razin Khan

This file records what has been built, what is still open, and what the next person needs to know. Update it after every piece of work.

---

## 1. Status summary

| Area | Status |
|---|---|
| Calculation engine folder structure | Done |
| `CALCULATION_ENGINE.md` documentation | Done (draft, see section 7 for items to update) |
| Methodologies METH-001, METH-002, METH-003 | Done, all marked `DRAFT_PENDING_REVIEW` |
| Factor files | Done, factors are placeholders pending review. `wood_density.json` is an empty template |
| Input validation | Done |
| Calculation records (audit trail, versioning, duplicate protection) | Done |
| Calculators: tree monitoring, soil carbon, tree carbon | Done |
| Automated tests | 50 tests written. Expected result: 50 passed |
| Uncertainty module | Not built (`uncertainty/` is empty) |
| Single entry point that selects a calculator by methodology ID | Not built |
| CSV and JSON export of calculation records | Not built |
| Dashboard integration | Not started (0%) |
| Python API | Not started |
| PDF export | Not started |
| Deployment changes | Not started |

---

## 2. How to run the engine

Python 3.10 or newer is needed. Run every command from the repository root.

```
pip install pytest
python -m pytest calculation_engine/tests -v
python -m calculation_engine.calculators.tree_monitoring_calculator
python -m calculation_engine.calculators.soil_carbon_calculator
python -m calculation_engine.calculators.tree_carbon_calculator
```

Each calculator's demo creates a real record in `calculation_engine/calculation_records/`. Running the same demo twice is blocked as a duplicate. The demos use invented sample data. Move demo records into `calculation_engine/examples/` so they are not mistaken for project results.

---

## 3. Key design decisions

- **Formulas live in data files, calculators read them.** Methodologies are in `methodologies/`, constants are in `factors/`. The record stores the exact formula text used.
- **An observation is a flat dictionary.** Reserved keys: `observation_id`, `project_type`, `evidence_reference`, `units`. Everything else is an input value for the methodology.
- **Validation is a gatekeeper.** If it fails, nothing is calculated and no record is created.
- **Records are never overwritten.** Each run creates a new file (`CALC-000001.json` and so on).
- **Duplicates are checked per methodology version and engine version.** The same observation can be recalculated under a new methodology or engine version, and both records are kept.
- **Missing evidence is a warning, not an error.** HR can change this to a blocking error if wanted.
- **Units are not converted automatically.** A value in the wrong unit is rejected.
- **Nothing is invented.** Uncertainty is left unstated unless a reviewer adds `default_uncertainty_percent` to the methodology file. Unapproved factors raise `UNAPPROVED_FACTOR` warnings in every record.
- **Equations are Python functions**, registered in `calculators/biomass_equations.py` by equation ID. They are not evaluated from text.

---

## 4. Values waiting for review by a domain expert

None of these are approved. Results are marked `QA_PENDING` and carry warnings until they are.

| Item | File | Current value | Issue |
|---|---|---|---|
| Biomass equation EQ-001 | `factors/biomass_factors/allometric_equations.json` | Chave et al. 2014 pantropical | Suitability for the project species and region is unconfirmed |
| Root to shoot ratio | `factors/biomass_factors/root_shoot_ratios.json` | 0.24 (placeholder) | Confirm against a source table |
| Carbon fraction | `factors/biomass_factors/carbon_fractions.json` | 0.47 | Species and region values should replace this where available |
| Wood density | `factors/biomass_factors/wood_density.json` | Empty template | Needs species list and sourced values |
| Validation limits | `validation/rules.json` | Sanity limits chosen by the author | Need review |
| Default uncertainty | `methodologies/agroforestry_carbon/METH-001.json` | None | Reviewer must supply a value |

---

## 5. Findings from the existing web dashboard (`index.html` on main)

The dashboard is one static HTML page using Tailwind, Chart.js, Leaflet and Google Fonts from CDNs, plus plain JavaScript. It has no backend and no connection to the calculation engine.

| Part | Status |
|---|---|
| Weather bar | Live fetch from Open-Meteo. Falls back to typed-in numbers on failure. Solar value falls back to 420 W/m2 |
| KPI cards | Hard-coded |
| Sequestration chart | Hard-coded arrays. The zone dropdown swaps between them |
| Map | Fixed polygons and fixed popup numbers |
| Ledger table | Three typed-in rows. The first row's oxygen and biomass values are replaced with random numbers every 3.5 seconds |
| CSV export | Works, but exports the placeholder table |
| PDF export | Missing |
| User input forms | Missing |

Items to fix or label before the dashboard is shown as real data:
- The "Open-Meteo: Connected" badge is hard-coded and stays green even when the fetch fails.
- The random ledger values are labelled "Verified".
- "Tier-1 Verified" and "cryptographically verifiable" are not supported by the system. Engine V1 does not claim third party verification.
- Chart.js is loaded unpinned. The Tailwind CDN is not intended for production use.

---

## 6. Open questions and decisions needed

1. Should this branch be merged into `main` through a pull request? HR decides.
2. Should the engine connect to the existing `carbon_engine` folder in `mrv_framework`? (see section 8)
3. Where will a Python API be hosted, and who pays for it? GitHub Pages cannot run Python.
4. Who approves the biomass equation, the factors and the validation limits?
5. How should the dashboard's unverified claims and placeholder data be labelled or replaced?

---

## 7. Remaining work for the next person

1. Build the uncertainty module and a single entry point that selects the calculator by methodology ID.
2. Build CSV and JSON export of calculation records, keeping the link between inputs, methodology and result.
3. Build a small FastAPI service around the engine, with input validation and clear error messages.
4. Add an input form and live results to the dashboard, and replace or clearly label the hard-coded values.
5. Add PDF export.
6. Review the GitHub Actions workflow and deployment, and set up hosting for the API.
7. Test with real data once factors are approved.
8. Update `CALCULATION_ENGINE.md` to match what was built: the observation format, the record fields `factors_used` and `warnings`, and the `UNAPPROVED_FACTOR` and `DEFAULT_APPLIED` warnings.

---

## 8. Repository findings

**GitHub Actions workflow.**
File: .github/workflows/ (deploy static content to Pages). It runs on pushes to
main and on manual start, and deploys the whole repository as a static site to
GitHub Pages. It does not build anything, run Python, or run tests. Pushes to
calculation-engine-v1 do not deploy.

**Existing carbon_engine.**
mrv_framework/mrv_framework/carbon_engine is a design document (Layer ID
MBF-dMRV-CARBON-001, version 0.1 Draft), not code. It describes the purpose and
objectives of a carbon intelligence layer. It has no implementation, so it does not
duplicate calculation_engine/, which can serve as the first implementation of that layer.

**Live dashboard address.**
Not confirmed. The author does not have admin access to the repository
settings. The address is visible under Deployments (github-pages) on the repository page.

**Power BI file.** The repository root holds the extracted internals of a `.pbix` file (`DataModel`, `Metadata`, `Settings`, `Version`, `SecurityBindings`, `DiagramLayout`, `[Content_Types].xml`). To open it, zip only those files, rename the zip to `.pbix`, and make sure the name does not end in `.pbix.zip`. A complete `.pbix` file may be available from the repository owner.

---

## 9. Change log

| Date | Change |
|---|---|
| 2026-11-01 | Handover file created. Engine V1 uploaded to branch `calculation-engine-v1` |
