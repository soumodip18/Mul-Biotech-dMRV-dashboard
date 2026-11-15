# Sample datasets

One example input and one expected output for each calculator.

**All data in this folder is made up for demonstration. It is not real project data, and the results are calculated values that have not been verified or reviewed.**

| Calculator | Methodology | Input file | Expected output file |
|---|---|---|---|
| Tree monitoring | METH-003 | `meth-003_tree_monitoring_input.json` | `meth-003_tree_monitoring_expected_output.json` |
| Soil organic carbon | METH-002 | `meth-002_soil_carbon_input.json` | `meth-002_soil_carbon_expected_output.json` |
| Tree and agroforestry carbon | METH-001 | `meth-001_tree_carbon_input.json` | `meth-001_tree_carbon_expected_output.json` |

## Run a sample

From the repository root:

    python -m calculation_engine.engine METH-003 calculation_engine/samples/meth-003_tree_monitoring_input.json

This saves a real record in `calculation_engine/calculation_records/`. Running the same sample twice is blocked as a duplicate. Delete or move sample records out of that folder so they are not mistaken for project results.

## How these files are checked

`tests/test_samples.py` runs every sample input through the engine and compares the result with the expected output, and also checks the key numbers against independent hand calculations. If a factor or methodology changes on purpose (for example when an expert approves a value), the expected output must be updated on purpose too.

## Expected warnings

The expected output lists warning codes the engine should raise. For example, `UNAPPROVED_FACTOR` appears because the biomass equation and root to shoot ratio are still pending expert review. When those are approved, the warnings will change.