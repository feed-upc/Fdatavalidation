# HELEADE Data Product

Synthetic dataset for the **HELEADE** territorial data space: the wetlands of southern Alicante, where protected-area managers, irrigation communities, salt producers and water managers share socio-environmental data to coordinate water-level operations with the breeding of sensitive bird species. It is designed to validate the four HELEADE Data Quality Requirements (DQR1HL–DQR4HL).

## Data Model

The dataset follows the HELEADE data model (see [`Metadata/UML.png`](Metadata/UML.png)):

```
Wetland                     → wetland.csv
 ├── MonitoringSite         → monitoring_site.csv
 │    ├── WaterLevelSeries  → water_level_series.csv
 │    └── Observation       → observation.csv
 │         ├── WaterLevelObservation    (observationType = waterLevel)
 │         ├── WeatherObservation       (observationType = weather)
 │         └── BiodiversityObservation  (observationType = biodiversity) → Species
 └── WaterManagementOperation → water_management_operation.csv
Species                     → species.csv
```

## File Structure

```
DataProduct_HELEADE/
├── Code/
│   └── generate_synthetic_data.py      # Synthetic data generator
├── Data/
│   ├── wetland.csv                     # 3 wetlands of southern Alicante
│   ├── monitoring_site.csv             # 17 monitoring sites with WKT locations
│   ├── species.csv                     # 3 bird species
│   ├── water_level_series.csv          # one hourly water-level series per site
│   ├── water_management_operation.csv  # 7 planned water-level operations
│   └── observation.csv                 # 510 water-level, weather and biodiversity observations
├── Metadata/
│   ├── UML.png                         # HELEADE data model (UML class diagram)
│   └── data_dictionary.md              # Every column, and where each defect is
└── README.md                           # This file
```

## Data Quality Requirements (DQRs)

| DQR        | Description                                                        | Pattern | Default data              |
| ---------- | ------------------------------------------------------------------ | ------- | ------------------------- |
| **DQR1HL** | Every monitoring site has a location                               | DQRP2   | Satisfied (17 of 17)      |
| **DQR2HL** | Observation times are written in UTC                               | DQRP3   | Violated (5 of 510 not in UTC) |
| **DQR3HL** | A "not detected" observation records no courtship, nesting or chicks | DQRP4 | Satisfied (0 of 79)       |
| **DQR4HL** | Every wetland has at least 5 monitoring sites                      | DQRP5   | Violated (La Mata has 4)  |

See [`Metadata/data_dictionary.md`](Metadata/data_dictionary.md) for the exact rows and columns.

## Reproducibility

Python 3.8+ and the standard library only:

```bash
cd DataProduct_HELEADE/
python3 Code/generate_synthetic_data.py                 # default data, as shipped
python3 Code/generate_synthetic_data.py --clean         # no defects: every DQR satisfied
python3 Code/generate_synthetic_data.py --all-defects   # every DQR violated
```

| Argument        | Default | Description                     |
| --------------- | ------- | ------------------------------- |
| `--seed`        | 7       | Random seed for reproducibility |
| `--output-dir`  | `Data/` | Output folder for the CSV files |
| `--clean`, `--all-defects` | — | Turn every defect off, or on |

The generator prints each DQR's defect count and an MD5 checksum per file; the same seed always gives identical files.

Wetlands, sites and observations are drawn exactly as the DQVP pipeline's own generator draws them, so `wetland.csv`, `monitoring_site.csv` and the first eight columns of `observation.csv` equal the data in the DQR catalogue's `tools/dqvp/data/heleade/`. Validating either folder gives the same results.

## Validation Services

The HELEADE validation services are in the DQR catalogue (`FederatedComputationalGovernance/ComputationalCatalogues/services/heleade/`). Each one reads this folder:

```bash
docker build -t dqr4hl FederatedComputationalGovernance/ComputationalCatalogues/services/heleade/DQR4HL
docker run --rm -v "$PWD/DataProductLayer/DataProduct_HELEADE/Data":/data dqr4hl /data
```
