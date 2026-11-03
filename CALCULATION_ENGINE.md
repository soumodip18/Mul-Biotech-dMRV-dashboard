# Mul Biotech dMRV Calculation Engine

**Engine version:** v0.1.0 (V1, computational foundation)
**Status:** In development

---

## 1. Purpose and Scope

The Calculation Engine converts validated project observations into traceable environmental and MRV (Measurement, Reporting and Verification) results. It exists so that no formula is hard coded inside the dashboard. The dashboard only displays results that the engine has already calculated and recorded.

**In scope for V1**
- Tree and agroforestry carbon (METH-001)
- Soil organic carbon (METH-002)
- Tree survival and biomass monitoring (METH-003)
- Input validation, calculation records, versioning and tests

**Out of scope for V1**
- Carbon credit issuance
- Any claim of formal third party verification

This release is the computational and MRV foundation only.

---

## 2. Architecture

```
calculation_engine/
├── methodologies/        Rulebook: formula, inputs, units, version per methodology
│   ├── agroforestry_carbon/
│   ├── soil_carbon/
│   └── tree_monitoring/
├── factors/              Constants used by formulas, stored with their own versions
│   ├── emission_factors/
│   ├── conversion_factors/
│   └── biomass_factors/
├── calculators/          Python code that runs the calculations
├── validation/           Checks inputs before any calculation runs
├── uncertainty/          Error range logic
├── calculation_records/  Permanent record of every calculation (never overwritten)
└── tests/                Automated tests
```

Design principle: **formulas and factors live in data files, calculators read them.** This allows a formula or constant to be updated and versioned without rewriting calculator code, and every result can be traced to the exact version used.

---

## 3. Workflow: Input to Validation to Calculation to Output

```
Field / Sensor / GIS Data
        |
Observation Layer
        |
Validation
        |
Calculation Engine
        |
Calculation Record
        |
QA / Verification
        |
Dashboard
        |
MRV Report
```

1. **Input:** a project observation with an ID, project ID, values, units and evidence reference.
2. **Validation:** the observation is checked. Failed checks stop the calculation and return clear errors.
3. **Calculation:** the matching approved methodology and factors are loaded and the formula is applied.
4. **Output:** a result with unit, uncertainty and methodology version.
5. **Record:** a permanent calculation record is saved with status `QA_PENDING`.
6. **Consumption:** the dashboard reads the record. It does not recalculate.

---

## 4. Methodology Registry

Each methodology is stored as a structured file (JSON) inside its folder under `methodologies/`. Every methodology must contain:

| Field | Description |
|---|---|
| Methodology ID | Unique ID, e.g. METH-001 |
| Name | Human readable name |
| Version | e.g. 1.0 |
| Applicable project types | Project types the methodology can be used for |
| Required inputs | Inputs that must be present |
| Optional inputs | Inputs that improve the result but are not mandatory |
| Formula | The exact formula applied |
| Units | Expected unit for each input and the output |
| Factors used | References to factor files and their versions |
| Data sources | Where inputs and factors come from |
| Assumptions | Assumptions the method relies on |
| Uncertainty rules | How uncertainty is estimated |
| Applicability conditions | Conditions under which the method is valid |
| Effective date | Date the version becomes valid |
| Limitations | Known limits of the method |

**Initial methodologies**

| ID | Name | Calculator |
|---|---|---|
| METH-001 | Agroforestry / Tree Biomass Carbon | Tree/Agroforestry Carbon |
| METH-002 | Soil Organic Carbon | Soil Organic Carbon |
| METH-003 | Tree Survival and Biomass Monitoring | Tree Monitoring |

**Reference formulas (to be confirmed by a methodology reviewer before approval)**

- Survival Rate (%) = Surviving Trees / Planted Trees x 100
- SOC stock (t C/ha) = SOC (%) x Bulk density (g/cm3) x Depth (cm) x (1 - Gravel fraction)
- CO2e = Carbon stock x 44/12
- Tree biomass equations, root to shoot ratios and carbon fractions are species and region dependent and must be selected and approved by someone with domain expertise. They are not fixed in this document.

---

## 5. Unit Handling

- Every input carries an explicit unit.
- Inputs are converted to the methodology's base units using values in `factors/conversion_factors/`.
- Conversions are logged in the calculation record.
- Unknown or incompatible units cause a validation error. The engine never guesses a unit.

---

## 6. Data Provenance

Every input and factor must be traceable. Records retain:

`Source > Source Type > Timestamp > Location > Processing Method > Model/Sensor > Confidence > Last Updated`

Source types are kept distinct: sensor observed, laboratory, satellite derived, weather provider, farmer reported, modelled, calculated, and AI inferred. Modelled or calculated values are never presented as direct field observations.

---

## 7. Uncertainty Handling

- Each calculator returns an uncertainty value together with the result.
- The uncertainty rule is defined in the methodology and implemented in `uncertainty/`.
- Results are reported in the form: value, unit and uncertainty (for example 18.42 tCO2e with a stated range).
- If uncertainty cannot be estimated, the result is flagged rather than reported as exact.

---

## 8. Version Control

Three things are versioned: the engine, each methodology, and each factor file.

- Historical calculations are **never overwritten**.
- A recalculation under a new engine or methodology version creates a **new** record.
- Both old and new records remain accessible.

Example:

```
CALC-001  Engine v0.1  Methodology v1.0  ->  18.42 tCO2e
CALC-045  Engine v0.2  Methodology v1.1  ->  19.13 tCO2e
```

---

## 9. Audit Trail

Every calculation creates a unique record in `calculation_records/`:

| Field | Example |
|---|---|
| Calculation ID | CALC-000001 |
| Project ID | MBF-DMRV-2026-001 |
| Methodology ID | METH-001 |
| Methodology Version | 1.0 |
| Input Observation IDs | list of IDs |
| Input Values | exact values and units used |
| Formula | exact formula applied |
| Result | numeric result |
| Unit | tCO2e |
| Uncertainty | value or range |
| Status | QA_PENDING |
| Calculated At | timestamp |
| Engine Version | v0.1.0 |

**Traceability goal:** Result > Formula > Methodology > Input data > Evidence > Version > Audit record.

---

## 10. Error Handling

The validation layer flags:

- Missing inputs
- Invalid units
- Negative values where impossible
- Duplicate observations
- Out of range values
- Missing methodology
- Missing evidence
- Incompatible methodology and project type

On failure the engine does not produce a result. It returns a structured error describing what failed and which input caused it. Failed runs may be logged for audit purposes but are never presented as results.

---

## 11. Limitations

- V1 does not issue carbon credits or claim third party verification.
- Results are only as reliable as the input observations and factors used.
- Biomass equations and factors must be matched to species and region, and V1 does not validate scientific suitability automatically.
- Uncertainty estimates in V1 are simplified and do not replace a full uncertainty analysis.
- All results start as `QA_PENDING` and require review before use in reporting.

---

## 12. Future Methodology Expansion

New methodologies are added by:

1. Creating a methodology file in `methodologies/` with all registry fields.
2. Adding any new factors under `factors/` with versions.
3. Adding a calculator in `calculators/` and validation rules in `validation/`.
4. Writing tests in `tests/` before approval.

Possible future areas include biochar, soil amendments, water and aquaculture metrics, and integration with the wider platform.
