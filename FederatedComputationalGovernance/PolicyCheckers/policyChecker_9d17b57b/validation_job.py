import great_expectations

import great_expectations as gx
import pandas as pd

def run_gx_validation(data_path):
    context = gx.get_context(mode='ephemeral')
    suite = context.suites.add(gx.ExpectationSuite(name='semantic_suite'))

    # Step 2: http://www.semanticweb.org/acraf/ontologies/2024/healthmesh/abox#CheckFreshness
    suite.add_expectation(gx.expectations.ExpectColumnValuesToBeBetween(**{'column': 'lastUpdated', 'min_value': 0, 'max_value': 30}))

    csv_asset = context.data_sources.add_pandas('pandas_source').add_csv_asset('csv_asset', filepath_or_buffer=data_path)
    batch_def = csv_asset.add_batch_definition_whole_dataframe('dataframe_batch_def')
    validation_definition = gx.ValidationDefinition(name='semantic_validation', data=batch_def, suite=suite)
    context.validation_definitions.add(validation_definition)
    checkpoint = gx.Checkpoint(name='semantic_checkpoint', validation_definitions=[validation_definition])
    context.checkpoints.add(checkpoint)
    result = checkpoint.run()
    return result.success


if __name__ == "__main__":
    import sys
    # Extract data path from args or use default
    data_file = sys.argv[1] if len(sys.argv) > 1 else "/home/acraf/psr/Fdatavalidation-1/DataProductLayer/DataProduct_EHDS_AMR/Data/Patient_Summary.csv"
    print(f"Loading data from {data_file}...")
    try:
        result = run_gx_validation(data_file)
        print("\n=== VALIDATION RESULT ===")
        print(result)
        print("===========================")
    except Exception as e:
        print(f"Error during validation: {e}")
        sys.exit(1)
