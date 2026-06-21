import great_expectations as gx
import pandas as pd

def run_gx_validation(data_path):
    # DQR5EH: Fairness check on gender column
    # Metric: max deviation from uniform distribution (%) — consistent with ImpQualityMetricFairness
    # Derived from ODRL: target=gender, operator=odrl:lt, rightOperand=5, unit=qudt:PERCENT
    attr = 'gender'
    threshold = 5  # percValue from ODRL odrl:rightOperand

    df = pd.read_csv(data_path)
    n_groups = df[attr].nunique()
    fairness_score = (df[attr].value_counts(normalize=True).max() - 1 / n_groups) * 100
    return fairness_score < threshold  # odrl:lt


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
