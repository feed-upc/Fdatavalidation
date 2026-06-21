# EHDS AMR Data Product

Synthetic dataset for the **European Health Data Space (EHDS)** antimicrobial resistance (AMR) surveillance use case. Designed to validate Data Quality Requirements (DQRs) in a cross-border health data interoperability scenario.

## Purpose

This data product provides a **reproducible, paper-quality** synthetic dataset that:

1. Conforms to the EHDS data model (Patient Summary + AMR entities)
2. Contains **deterministic data quality violations** for testing six DQRs (DQR1EH–DQR6EH)
3. Supports validation of the federated data quality governance framework

## Data Model

The dataset follows the EHDS UML class diagram (see [`Metadata/UML.png`](Metadata/UML.png)):

```
PatientSummary
 ├── PatientIdentification   → Patient_Summary.csv
 ├── Allergy                 → Allergy.csv
 ├── PregnancyHistory        → Pregnancy_History.csv
 └── Hospital                → Hospital.csv

IsolateHistory
 ├── Isolate                 → Isolate.csv
 └── AMRStudy                → AMR_Study.csv
```

## File Structure

```
DataProduct_EHDS_AMR/
├── Code/
│   └── generate_synthetic_data.py   # Synthetic data generator
├── Data/
│   ├── Patient_Summary.csv          # Patient demographics & identifiers
│   ├── Hospital.csv                 # Hospital reference data (EU-27)
│   ├── Pregnancy_History.csv        # Pregnancy records per patient
│   ├── Allergy.csv                  # Patient allergy information
│   ├── Isolate.csv                  # AMR isolate-level test results
│   └── AMR_Study.csv                # Aggregate study metadata
├── Metadata/
│   ├── UML.png                      # EHDS data model (UML class diagram)
│   ├── data_dictionary.md           # Full schema & violation documentation
│   ├── usecase.md                   # Use case description for the paper
│   └── *.pdf                        # eHN Patient Summary guidelines
└── README.md                        # This file
```

## Data Quality Requirements (DQRs)

Six DQRs are defined by the EHDS Data Space Governance Authority. Violations are injected **deterministically** at fixed row indices to ensure reproducibility:

| DQR        | Description                                         | Dimension          | Violation Count            |
| ---------- | --------------------------------------------------- | ------------------ | -------------------------- |
| **DQR1EH** | Patient ID must not be null                         | Completeness       | 5                          |
| **DQR2EH** | Affiliation country must be a valid ISO 3166 code   | Compliance         | 10                         |
| **DQR3EH** | Male patients shall not have pregnancy records      | Consistency        | 5                          |
| **DQR4EH** | Minimum 2,000 total isolates for reliable AMR rates | Sample Size        | Verified in AMR\_Study.csv |
| **DQR5EH** | Balanced male/female representation (1:1 ratio)     | Representativeness | First 250 rows: 60%M/40%F  |
| **DQR6EH** | Hospital country must be a valid ISO 3166 code      | Compliance         | 10                         |

See [`Metadata/data_dictionary.md`](Metadata/data_dictionary.md) for exact violation indices and column-level documentation.

## Reproducibility

### Prerequisites

- Python 3.8+
- No external dependencies (uses only the Python standard library)

### Generating the Data

```bash
cd DataProduct_EHDS_AMR/
python3 Code/generate_synthetic_data.py --seed 42 --num-patients 500 --num-specimens 500
```

### Generator Options

| Argument          | Default | Description                     |
| ----------------- | ------- | ------------------------------- |
| `--seed`          | 42      | Random seed for reproducibility |
| `--num-patients`  | 500     | Number of patient records       |
| `--num-specimens` | 500     | Number of AMR isolate specimens |
| `--output-dir`    | `Data/` | Output directory for CSV files  |

### Verification

The generator prints a **verification summary** including:

- Exact violation counts for each DQR
- Gender ratio breakdown (DQR5EH)
- Total isolate count and DQR4EH pass/fail status
- MD5 checksums for every generated file

Running the generator with the same seed will always produce **identical output**.

### Quick Verification Script

```python
import pandas as pd

# Load data
patients = pd.read_csv('Data/Patient_Summary.csv')
pregnancies = pd.read_csv('Data/Pregnancy_History.csv')
isolates = pd.read_csv('Data/Isolate.csv')
study = pd.read_csv('Data/AMR_Study.csv')

# DQR1EH: 5 null patient IDs
null_ids = (patients['nationalHealthcarePatientID'] == '').sum()
print(f"DQR1EH — NULL patient IDs: {null_ids} (expected: 5)")

# DQR2EH: 10 invalid affiliation countries
valid = set(["ES","FR","DE","IT","PT","NL","BE","AT","PL","CZ","GR","SE",
             "FI","DK","IE","RO","BG","HR","SK","SI","HU","LT","LV","EE",
             "CY","MT","LU"])
invalid_aff = (~patients['countryOfAffiliation'].isin(valid)).sum()
print(f"DQR2EH — Invalid affiliation countries: {invalid_aff} (expected: 10)")

# DQR3EH: 5 males with pregnancy
male_ids = set(patients[patients['gender'] == 'M']['nationalHealthcarePatientID'])
male_preg = pregnancies[pregnancies['patientID'].isin(male_ids)]['patientID'].nunique()
print(f"DQR3EH — Males with pregnancy records: {male_preg} (expected: 5)")

# DQR4EH: total isolates ≥ 2000
total = isolates['nIsolates'].sum()
print(f"DQR4EH — Total isolates: {total} (threshold: ≥ 2000)")

# DQR5EH: gender ratio
m_count = (patients['gender'] == 'M').sum()
f_count = (patients['gender'] == 'F').sum()
print(f"DQR5EH — Gender ratio: {m_count}M / {f_count}F ({m_count/len(patients)*100:.1f}% / {f_count/len(patients)*100:.1f}%)")

# DQR6EH: invalid hospital countries
invalid_hosp = (~patients['hospitalCountry'].isin(valid)).sum()
print(f"DQR6EH — Invalid hospital countries: {invalid_hosp} (expected: 10)")
```

## Data Generation Methodology

The synthetic data generation follows a **DQR-driven approach**:

1. **Schema Derivation**: Entity schemas are derived from the EHDS UML class diagram, covering Patient Identification, Hospital, Pregnancy History, Allergy, Isolate, and AMR Study.

2. **Attribute Population**: Attributes are populated using clinically plausible distributions:
   - Patient names from EU-27 cultural pools
   - Dates within realistic clinical ranges (birth: 1940–2005, specimens: 2023–2025)
   - Organisms and antibiotics from WHO priority pathogens lists
   - Resistance results following typical clinical distributions (~50% susceptible)

3. **Violation Injection**: Each DQR violation is injected at **fixed row indices** (not probabilistically), ensuring:
   - Exact reproducibility across runs
   - Known ground truth for automated validation
   - Clear mapping between violations and their DQR pattern

4. **Referential Integrity**: Foreign key relationships are maintained:
   - Pregnancy records reference valid patient IDs
   - Isolates reference valid patient IDs
   - Hospital codes in Patient\_Summary reference Hospital.csv entries

5. **Verification**: The generator outputs a complete verification summary with MD5 checksums, enabling independent validation of data integrity.

## References

- EHDS Regulation: [European Health Data Space](https://health.ec.europa.eu/ehealth-digital-health-and-care/european-health-data-space_en)
- eHN Patient Summary Guidelines: See `Metadata/ehn_guidelines_patientsummary_en (1).pdf`
- AMR Surveillance: ECDC/EARS-Net methodology
- ISO 3166-1: Country codes standard
- DQR Patterns: [DS-DataQualityRequirements](https://github.com/feed-upc/DS-DataQualityRequirements)
