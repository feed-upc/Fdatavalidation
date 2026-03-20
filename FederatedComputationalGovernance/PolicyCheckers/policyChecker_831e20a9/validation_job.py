import pycountry
import great_expectations

import great_expectations as gx
import pandas as pd

def run_gx_validation(data_path):
    context = gx.get_context(mode='ephemeral')
    suite = context.suites.add(gx.ExpectationSuite(name='semantic_suite'))

    # Step 2: http://www.semanticweb.org/acraf/ontologies/2024/healthmesh/abox#qM_Validity
    suite.add_expectation(gx.expectations.ExpectColumnValuesToBeInSet(**{'column': 'countryOfAffiliation', 'mostly': 1.0, 'value_set': ['AW', 'AF', 'AO', 'AI', 'AX', 'AL', 'AD', 'AE', 'AR', 'AM', 'AS', 'AQ', 'TF', 'AG', 'AU', 'AT', 'AZ', 'BI', 'BE', 'BJ', 'BQ', 'BF', 'BD', 'BG', 'BH', 'BS', 'BA', 'BL', 'BY', 'BZ', 'BM', 'BO', 'BR', 'BB', 'BN', 'BT', 'BV', 'BW', 'CF', 'CA', 'CC', 'CH', 'CL', 'CN', 'CI', 'CM', 'CD', 'CG', 'CK', 'CO', 'KM', 'CV', 'CR', 'CU', 'CW', 'CX', 'KY', 'CY', 'CZ', 'DE', 'DJ', 'DM', 'DK', 'DO', 'DZ', 'EC', 'EG', 'ER', 'EH', 'ES', 'EE', 'ET', 'FI', 'FJ', 'FK', 'FR', 'FO', 'FM', 'GA', 'GB', 'GE', 'GG', 'GH', 'GI', 'GN', 'GP', 'GM', 'GW', 'GQ', 'GR', 'GD', 'GL', 'GT', 'GF', 'GU', 'GY', 'HK', 'HM', 'HN', 'HR', 'HT', 'HU', 'ID', 'IM', 'IN', 'IO', 'IE', 'IR', 'IQ', 'IS', 'IL', 'IT', 'JM', 'JE', 'JO', 'JP', 'KZ', 'KE', 'KG', 'KH', 'KI', 'KN', 'KR', 'KW', 'LA', 'LB', 'LR', 'LY', 'LC', 'LI', 'LK', 'LS', 'LT', 'LU', 'LV', 'MO', 'MF', 'MA', 'MC', 'MD', 'MG', 'MV', 'MX', 'MH', 'MK', 'ML', 'MT', 'MM', 'ME', 'MN', 'MP', 'MZ', 'MR', 'MS', 'MQ', 'MU', 'MW', 'MY', 'YT', 'NA', 'NC', 'NE', 'NF', 'NG', 'NI', 'NU', 'NL', 'NO', 'NP', 'NR', 'NZ', 'OM', 'PK', 'PA', 'PN', 'PE', 'PH', 'PW', 'PG', 'PL', 'PR', 'KP', 'PT', 'PY', 'PS', 'PF', 'QA', 'RE', 'RO', 'RU', 'RW', 'SA', 'SD', 'SN', 'SG', 'GS', 'SH', 'SJ', 'SB', 'SL', 'SV', 'SM', 'SO', 'PM', 'RS', 'SS', 'ST', 'SR', 'SK', 'SI', 'SE', 'SZ', 'SX', 'SC', 'SY', 'TC', 'TD', 'TG', 'TH', 'TJ', 'TK', 'TM', 'TL', 'TO', 'TT', 'TN', 'TR', 'TV', 'TW', 'TZ', 'UG', 'UA', 'UM', 'UY', 'US', 'UZ', 'VA', 'VC', 'VE', 'VG', 'VI', 'VN', 'VU', 'WF', 'WS', 'YE', 'ZA', 'ZM', 'ZW']}))

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
