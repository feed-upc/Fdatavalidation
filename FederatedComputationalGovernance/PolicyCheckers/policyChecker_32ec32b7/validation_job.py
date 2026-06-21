import great_expectations
import pycountry

import great_expectations as gx
import pandas as pd

def run_gx_validation(data_path):
    context = gx.get_context(mode='ephemeral')
    suite = context.suites.add(gx.ExpectationSuite(name='semantic_suite'))

    # Step 2: http://www.semanticweb.org/acraf/ontologies/2024/healthmesh/abox#qM_Validity
    # DQR6EH: Compliance check on Hospital.country column against ISO 3166 alpha-2
    # Derived from ODRL: target=Hospital.country, operator=odrl:isIncludedIn, rightOperand=ab:ISO_3166_International_Standard
    iso_3166_alpha2 = {country.alpha_2 for country in pycountry.countries}
    suite.add_expectation(gx.expectations.ExpectColumnValuesToBeInSet(**{'column': 'country', 'mostly': 1.0, 'value_set': sorted(iso_3166_alpha2)}))

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
    data_file = sys.argv[1] if len(sys.argv) > 1 else "/home/acraf/psr/Fdatavalidation-1/DataProductLayer/DataProduct_EHDS_AMR/Data/Hospital.csv"
    print(f"Loading data from {data_file}...")
    try:
        result = run_gx_validation(data_file)
        print("\n=== VALIDATION RESULT ===")
        print(result)
        print("===========================")
    except Exception as e:
        print(f"Error during validation: {e}")
        sys.exit(1)
