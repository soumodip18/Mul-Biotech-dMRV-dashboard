# Handover: Mul Biotech dMRV Calculation Engine and Dashboard

**Branch:** `calculation-engine-v1` (do not merge into `main` until the technical review is complete)
**Prepared by:** Razin
**Last updated:** see the commit history of this file on GitHub for exact dates

This file records what has been built, what is still open, and what the next developer needs to know. Update it after every piece of work.

---

## 1. Status summary

| Area | Status |
|---|---|
| Calculation engine folder structure | Done |
| `CALCULATION_ENGINE.md` documentation | Done as a first draft. Needs updating to match what was built (see section 7) |
| `ASSUMPTIONS_AND_FACTORS.md` | Done |
| Methodologies METH-001, METH-002, METH-003 | Done, all marked `DRAFT_PENDING_REVIEW` |
| Factor files | Done. Values are placeholders pending review. `wood_density.json` is an empty template |
| Input validation | Done |
| Calculation records (audit trail, versioning, duplicate protection) | Done |
| Calculators: tree monitoring, soil carbon, tree carbon | Done |
| Uncertainty module | Done. It states an uncertainty only when one is supplied or a reviewer adds a default |
| Single entry point (`engine.py`) that selects the calculator by methodology ID | Done |
| CSV and JSON export of records (`export.py`) | Done |
| Sample input and expected output for each calculator (`samples/`) | Done |
| Automated tests | 90 tests, all passing at the last full run |
| Python API (FastAPI) | Not started. Assigned to the next developer |
| Dashboard integration | Not started. Assigned to the next developer |
| PDF export | Not started |
| Deployment changes and API hosting | Not started |
| Expert approval of the biomass equation and factors | Waiting for review |

---

## 2. Folder map

```
calculation_engine/
├── engine.py                  Single entry point: run_calculation(methodology_id, observation)
├── export.py                  Writes JSON and CSV exports of calculation records
├── records.py                 Saves records (never overwrites) and detects duplicates
├── factor_loader.py           Reads factor files
├── methodologies/             METH-001, METH-002, METH-003 (formulas, inputs, units, limits)
├── factors/                   Constants: CO2 factor, biomass factors, unit conversions
├── calculators/               One calculator per methodology, plus biomass_equations.py
├── validation/                validator.py and rules.json (allowed ranges)
├── uncertainty/               build_uncertainty(): never invents a value
├── calculation_records/       Saved records (CALC-000001.json and so on)
├── exports/                   Generated exports. Ignored by Git on purpose
├── samples/                   Made up example inputs and expected outputs, with a README
├── examples/                  Example records from early demo runs (sample data only)
└── tests/                     90 automated tests
```

Other documents: `CALCULATION_ENGINE.md` (design), `ASSUMPTIONS_AND_FACTORS.md` (factors, assumptions and approval list), `calculation_engine/samples/README.md` (how to run the samples).

---

## 3. How to run the engine

Python 3.10 or newer is needed. Run every command from the repository root.

```
pip install pytest
python -m pytest calculation_engine/tests -v                 expected: 90 passed
python -m calculation_engine.engine                          list the methodologies
python -m calculation_engine.engine METH-003 calculation_engine/samples/meth-003_tree_monitoring_input.json
python -m calculation_engine.export                          write the exports
```

Running a calculation saves a real record in `calculation_engine/calculation_records/`. Running the same observation twice is blocked as a duplicate. After trying the samples, delete the sample records so they are not mistaken for project results.

---

## 4. How to use the engine from code (for the API developer)

```python
from calculation_engine.engine import run_calculation

outcome = run_calculation("METH-003", observation)
```

An observation is a flat dictionary. Reserved keys are `observation_id`, `project_type`, `evidence_reference` and `units`. Every other key is an input value for the methodology. See `calculation_engine/samples/` for one complete example per methodology, and the `required_inputs` of each methodology file for the exact input names and units.

`run_calculation` returns a dictionary with these keys:

| Key | Meaning |
|---|---|
| `status` | `QA_PENDING` (calculated and saved), `VALIDATION_FAILED` (nothing calculated, no record), or `NO_CALCULATOR` (methodology file exists but no calculator) |
| `validation` | `is_valid`, plus lists of `errors` and `warnings`. Each has `code`, `field` and `message` |
| `record` | The saved calculation record, or `None` if nothing was calculated |
| `file` | Path of the saved record file (only when a record was saved) |

Useful details:
- **Records folder.** `run_calculation(..., records_dir=...)` accepts a different folder. Real project records should be stored outside the public repository.
- **Error codes** include `MISSING_INPUT`, `INVALID_TYPE`, `NEGATIVE_VALUE`, `OUT_OF_RANGE`, `INVALID_UNIT`, `INVALID_RELATION`, `DUPLICATE_OBSERVATION`, `MISSING_METHODOLOGY`, `INCOMPATIBLE_PROJECT_TYPE`, `UNKNOWN_EQUATION` and `NO_CALCULATOR`.
- **Warning codes** include `MISSING_EVIDENCE`, `DEFAULT_APPLIED`, `UNAPPROVED_FACTOR`, `NO_STATED_UNCERTAINTY` and `INVALID_UNCERTAINTY`.
- **Keep the engine independent of the dashboard.** The API should import the engine, not the other way round.
- **For dashboard charts** the easiest input is `exports/calculation_results.csv` (one row per result value). `calculation_records.json` holds full records, and `calculation_records.csv` is a one row summary per calculation.
- **Adding a methodology:** add a `METH-xxx.json` file, a calculator in `calculators/`, an entry in the `CALCULATORS` dictionary in `engine.py`, validation limits in `validation/rules.json`, a sample, and tests.

---

## 5. Key design decisions

- **Formulas live in data files, calculators read them.** The record stores the exact formula text used.
- **Validation is a gatekeeper.** If it fails, nothing is calculated and no record is created.
- **Records are never overwritten.** Each run creates a new file.
- **Duplicates are checked per methodology version and engine version.** The same observation can be recalculated under a new version, and both records are kept.
- **Missing evidence is a warning, not an error.** HR can change this to a blocking error if wanted.
- **Units are not converted automatically.** A value in the wrong unit is rejected.
- **Nothing is invented.** Uncertainty is left unstated unless a laboratory value is supplied with the observation (`lab_uncertainty_percent`, soil only) or a reviewer adds `default_uncertainty_percent` and `uncertainty_applies_to` to the methodology file. Unapproved factors raise `UNAPPROVED_FACTOR` warnings in every record.
- **Equations are Python functions**, registered by equation ID in `calculators/biomass_equations.py`. They are not evaluated from text.
- **Exports are derived data.** They only read records. They carry a notice that nothing in them is a verified carbon credit, and text that looks like a spreadsheet formula is neutralised.
- **Generated exports are ignored by Git** (`exports/.gitignore`), because they can contain project data.

---

## 6. Values waiting for review by a domain expert

None of these are approved. Results are marked `QA_PENDING` and carry warnings until they are. The full list with explanations is in `ASSUMPTIONS_AND_FACTORS.md`.

| Item | File | Current value | Issue |
|---|---|---|---|
| Biomass equation EQ-001 | `factors/biomass_factors/allometric_equations.json` | Chave et al. 2014 pantropical | Suitability for the project species and region is unconfirmed |
| Root to shoot ratio | `factors/biomass_factors/root_shoot_ratios.json` | 0.24 (placeholder) | Confirm against a source table |
| Carbon fraction | `factors/biomass_factors/carbon_fractions.json` | 0.47 | Species and region values should replace this where available |
| Wood density | `factors/biomass_factors/wood_density.json` | Empty template | Needs species list and sourced values |
| Validation limits | `validation/rules.json` | Sanity limits chosen by the author | Need review |
| Default uncertainty | `methodologies/agroforestry_carbon/METH-001.json` and `methodologies/soil_carbon/METH-002.json` | None | Reviewer must supply a value |
| Methodology status | All three methodology files | `DRAFT_PENDING_REVIEW` | None are approved |

When a value is approved: update the factor file, raise its version, update the sample expected outputs on purpose, run the tests, and record the approver here.

---

## 7. Remaining work for the next developer

1. Build a small FastAPI service around `run_calculation`, with input validation and clear error messages. Choose a host (GitHub Pages cannot run Python).
2. Add an input form and live results to the dashboard.
3. Replace or clearly label the hard coded and simulated values on the dashboard (section 8).
4. Add PDF export.
5. Add tests that run before deployment, and review the deployment workflow.
6. Update `CALCULATION_ENGINE.md` to match what was built: the flat observation format, the record fields `factors_used` and `warnings`, the warning codes, the entry point, uncertainty, export and samples.
7. Test with real data once factors are approved, and decide where real calculation records are stored.
8. Decide whether `calculation_records/CALC-*.json` should be ignored by Git, so real project records are never committed to a public repository.

---

## 8. Findings from the existing web dashboard (`index.html` on main)

The dashboard is one static HTML page using Tailwind, Chart.js, Leaflet and Google Fonts from CDNs, plus plain JavaScript. It has no backend and no connection to the calculation engine.

| Part | Status |
|---|---|
| Weather bar | Live fetch from Open-Meteo. Falls back to typed in numbers on failure. Solar value falls back to 420 W/m2 |
| KPI cards | Hard coded |
| Sequestration chart | Hard coded arrays. The zone dropdown swaps between them |
| Map | Fixed polygons and fixed popup numbers |
| Ledger table | Three typed in rows. The first row's oxygen and biomass values are replaced with random numbers every 3.5 seconds |
| CSV export | Works, but exports the placeholder table |
| PDF export | Missing |
| User input forms | Missing |

Items to fix or label before the dashboard is shown as real data:
- The "Open-Meteo: Connected" badge is hard coded and stays green even when the fetch fails.
- The random ledger values are labelled "Verified".
- "Tier-1 Verified" and "cryptographically verifiable" are not supported by the system. The engine does not claim third party verification.
- Chart.js is loaded unpinned. The Tailwind CDN is not intended for production use.

---

## 9. Repository findings

**GitHub Actions workflow.**
File: `.github/workflows/static.yml` (deploy static content to Pages). It runs on pushes to `main` and on manual start, and deploys the whole repository as a static site to GitHub Pages. It does not build anything, run Python, or run tests. Pushes to `calculation-engine-v1` do not deploy.

**Existing `carbon_engine`.**
`mrv_framework/mrv_framework/carbon_engine` is a design document (Layer ID MBF-dMRV-CARBON-001, version 0.1 Draft), not code. It describes the purpose and objectives of a carbon intelligence layer. It has no implementation, so it does not duplicate `calculation_engine/`, which can serve as the first implementation of that layer.

**Live dashboard address.**
Not confirmed. The author does not have admin access to the repository settings. The address is visible under Deployments (github-pages) on the repository page.

**Branch status.**
On GitHub the branch showed "1 commit ahead of and 1 commit behind `main`". The commit on `main` has not been inspected. Check it before the technical review.

**Power BI file.** The repository root holds the extracted internals of a `.pbix` file (`DataModel`, `Metadata`, `Settings`, `Version`, `SecurityBindings`, `DiagramLayout`, `[Content_Types].xml`). To open it, zip only those files, rename the zip to `.pbix`, and make sure the name does not end in `.pbix.zip`. A complete `.pbix` file may be available from the repository owner.

---

## 10. Open questions and decisions needed

1. Should this branch be merged into `main` through a pull request, and when? (Not before the technical review.)
2. Where will a Python API be hosted, and who pays for it?
3. Who approves the biomass equation, the factors and the validation limits?
4. How should the dashboard's unverified claims and placeholder data be labelled or replaced?
5. A central GIS and geospatial datasets repository has been announced. Shared reference data should come from it once it exists. Factor files already go through `factor_loader.py`, so only that loader would need to change. Records could also store a dataset ID and version.

---

## 11. Change log

See the commit history of this file on GitHub for exact dates.

| Order | Change |
|---|---|
| 1 | Handover file created. Engine V1 uploaded to branch `calculation-engine-v1` |
| 2 | Uncertainty module and engine entry point added. Tests increased to 73 |
| 3 | CSV and JSON export, sample datasets and sample tests added. Tests increased to 90 |
| 4 | `ASSUMPTIONS_AND_FACTORS.md` added |
| 5 | Final handover update: status, folder map, API guidance, remaining work |
