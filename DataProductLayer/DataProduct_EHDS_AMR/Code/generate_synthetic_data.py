#!/usr/bin/env python3
"""
Synthetic Data Generator for the EHDS AMR Data Product
=======================================================

Generates synthetic datasets aligned with the European Health Data Space (EHDS)
data model for antimicrobial resistance (AMR) surveillance. The generated data
contains intentional, deterministic quality violations designed to test six
Data Quality Requirements (DQR1EH–DQR6EH) defined by the EHDS Data Space
Governance Authority.

Data Model Reference:
    The generated tables correspond to the entities in the EHDS UML class diagram
    (see Metadata/UML.png), covering Patient Identification, Hospital, Pregnancy
    History, Allergy, Isolate, and AMR Study information.

Violation Design:
    Violations are injected at **fixed row indices** (not probabilistically) to
    ensure exact reproducibility. A verification summary is printed after
    generation so that the ground truth can be cross-referenced in the paper.

Usage:
    python generate_synthetic_data.py [--seed 42] [--num-patients 500]
                                      [--num-specimens 500] [--output-dir ../Data]

Authors: UPC FEED Research Group
License: Apache-2.0
"""

import argparse
import csv
import hashlib
import os
import random
import sys
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Valid ISO 3166-1 alpha-2 country codes (EU-27 Member States)
VALID_COUNTRIES = [
    "ES", "FR", "DE", "IT", "PT", "NL", "BE", "AT", "PL", "CZ",
    "GR", "SE", "FI", "DK", "IE", "RO", "BG", "HR", "SK", "SI",
    "HU", "LT", "LV", "EE", "CY", "MT", "LU",
]

# Invalid codes used for DQR2EH / DQR6EH violations
INVALID_COUNTRIES = ["XX", "ZZ", "123", "ABC", "EU", ""]

# Clinically relevant organisms for AMR surveillance
ORGANISMS = [
    "Escherichia coli",
    "Klebsiella pneumoniae",
    "Staphylococcus aureus",
    "Pseudomonas aeruginosa",
    "Enterococcus faecium",
    "Acinetobacter baumannii",
]

# Antimicrobial agents commonly tested
ANTIBIOTICS = [
    "Amoxicillin",
    "Ciprofloxacin",
    "Vancomycin",
    "Meropenem",
    "Gentamicin",
    "Colistin",
    "Tigecycline",
]

# Given name pools for synthetic patients
GIVEN_NAMES_M = [
    "Carlos", "Pierre", "Hans", "Marco", "João", "Jan", "Piotr", "Tomáš",
    "Nikos", "Erik", "Mikko", "Lars", "Sean", "Ion", "Georgi", "Ivan",
    "Matej", "Ádám", "Marius", "Jānis", "Martin", "Petros", "Luca", "Léon",
]
GIVEN_NAMES_F = [
    "María", "Marie", "Anna", "Giulia", "Ana", "Sophie", "Agnieszka", "Tereza",
    "Eleni", "Astrid", "Aino", "Ida", "Aoife", "Elena", "Tsvetana", "Katarina",
    "Zuzana", "Eszter", "Rūta", "Līga", "Marika", "Helena", "Emma", "Chloé",
]
FAMILY_NAMES = [
    "García", "Dupont", "Müller", "Rossi", "Silva", "De Groot", "Peeters",
    "Huber", "Kowalski", "Novák", "Papadopoulos", "Andersson", "Virtanen",
    "Nielsen", "Murphy", "Popescu", "Ivanov", "Kovačević", "Horváth", "Kalnins",
    "Jonaitis", "Georgiou", "Bianchi", "Martin", "Schmidt", "López",
]

# Allergy data pools (based on eHN Patient Summary guidelines)
ALLERGY_DESCRIPTIONS = [
    "Penicillin allergy", "Sulfonamide hypersensitivity", "Latex allergy",
    "Aspirin sensitivity", "Ibuprofen allergy", "Cephalosporin allergy",
    "Egg protein allergy", "Contrast dye reaction", "Codeine intolerance",
    "Pollen-food syndrome",
]
ALLERGY_AGENTS = [
    "Penicillin", "Sulfonamide", "Latex", "Aspirin", "Ibuprofen",
    "Cephalosporin", "Egg protein", "Iodinated contrast", "Codeine", "Pollen",
]
ALLERGY_SEVERITIES = ["Mild", "Moderate", "Severe", "Life-threatening"]
ALLERGY_CRITICALITIES = ["Low", "High", "Unable to assess"]
ALLERGY_STATUSES = ["Active", "Resolved", "Inactive"]
ALLERGY_TYPES = ["Allergy", "Intolerance"]
ALLERGY_MANIFESTATIONS = [
    "Urticaria", "Anaphylaxis", "Rash", "Bronchospasm", "Angioedema",
    "Gastrointestinal distress", "Contact dermatitis",
]

# City pools per country for Hospital generation
CITIES = {
    "ES": ["Madrid", "Barcelona", "Valencia", "Sevilla"],
    "FR": ["Paris", "Lyon", "Marseille", "Toulouse"],
    "DE": ["Berlin", "München", "Hamburg", "Köln"],
    "IT": ["Roma", "Milano", "Napoli", "Torino"],
    "PT": ["Lisboa", "Porto", "Coimbra", "Braga"],
    "NL": ["Amsterdam", "Rotterdam", "Utrecht", "Eindhoven"],
    "BE": ["Bruxelles", "Antwerpen", "Gent", "Liège"],
    "AT": ["Wien", "Graz", "Linz", "Salzburg"],
    "PL": ["Warszawa", "Kraków", "Wrocław", "Gdańsk"],
    "CZ": ["Praha", "Brno", "Ostrava", "Plzeň"],
    "GR": ["Athina", "Thessaloniki", "Patras", "Heraklion"],
    "SE": ["Stockholm", "Göteborg", "Malmö", "Uppsala"],
    "FI": ["Helsinki", "Espoo", "Tampere", "Turku"],
    "DK": ["København", "Aarhus", "Odense", "Aalborg"],
    "IE": ["Dublin", "Cork", "Galway", "Limerick"],
    "RO": ["București", "Cluj-Napoca", "Timișoara", "Iași"],
    "BG": ["Sofia", "Plovdiv", "Varna", "Burgas"],
    "HR": ["Zagreb", "Split", "Rijeka", "Osijek"],
    "SK": ["Bratislava", "Košice", "Prešov", "Žilina"],
    "SI": ["Ljubljana", "Maribor", "Celje", "Kranj"],
    "HU": ["Budapest", "Debrecen", "Szeged", "Miskolc"],
    "LT": ["Vilnius", "Kaunas", "Klaipėda", "Šiauliai"],
    "LV": ["Rīga", "Daugavpils", "Liepāja", "Jelgava"],
    "EE": ["Tallinn", "Tartu", "Narva", "Pärnu"],
    "CY": ["Nicosia", "Limassol", "Larnaca", "Paphos"],
    "MT": ["Valletta", "Birkirkara", "Mosta", "Qormi"],
    "LU": ["Luxembourg", "Esch-sur-Alzette", "Differdange", "Dudelange"],
}

# Pregnancy statuses for Pregnancy History
PREGNANCY_STATUSES = [
    "Delivered", "Miscarriage", "Ectopic", "Stillbirth",
]

# ---------------------------------------------------------------------------
# Violation Index Configuration
# ---------------------------------------------------------------------------
# Fixed indices (0-based) at which each DQR violation is injected.
# Using deterministic indices guarantees identical output across runs.

# DQR1EH: NULL patient IDs (Completeness) — 5 violations
DQR1_NULL_PATIENT_INDICES = [19, 115, 334, 410, 423]

# DQR2EH: Invalid affiliation country codes (Validity) — 10 violations
DQR2_INVALID_AFFILIATION_INDICES = [10, 35, 59, 62, 111, 190, 212, 328, 357, 497]

# DQR3EH: Males with pregnancy history (Consistency) — 5 violations
DQR3_MALE_PREGNANCY_INDICES = [138, 209, 220, 270, 363]

# DQR5EH: Gender imbalance — first 250 patients are 60% M / 40% F
# (structural, not per-index; implemented via generation logic)

# DQR6EH: Invalid hospital country codes (Validity) — 10 violations
DQR6_INVALID_HOSPITAL_INDICES = [46, 129, 193, 253, 264, 279, 383, 441, 462, 495]

# Invalid country assignment — cycles through INVALID_COUNTRIES
def _pick_invalid_country(idx, pool=INVALID_COUNTRIES):
    """Deterministically pick an invalid country code from the pool."""
    return pool[idx % len(pool)]


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def generate_date(rng, start_year=2020, end_year=2025):
    """Generate a random date string in YYYY-MM-DD format."""
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = end - start
    random_days = rng.randint(0, delta.days)
    return (start + timedelta(days=random_days)).strftime("%Y-%m-%d")


def generate_timestamp(rng, start_year=2024, end_year=2025):
    """Generate a random ISO 8601 timestamp."""
    date_str = generate_date(rng, start_year, end_year)
    hour = rng.randint(0, 23)
    minute = rng.randint(0, 59)
    return f"{date_str}T{hour:02d}:{minute:02d}:00Z"


def md5_file(filepath):
    """Compute MD5 checksum for a file."""
    h = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def write_csv(filepath, fieldnames, rows):
    """Write a list of dicts to CSV."""
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    count = len(rows)
    checksum = md5_file(filepath)
    print(f"  ✓ {os.path.basename(filepath):30s} — {count:>5d} rows  (MD5: {checksum})")
    return checksum


# ---------------------------------------------------------------------------
# Data Generators
# ---------------------------------------------------------------------------

def generate_hospitals(rng, num_hospitals=50):
    """
    Generate Hospital.csv

    Columns (from UML): hospitalCode, city, country
    DQR6EH violations are injected into Patient_Summary.hospitalCountry,
    not into the Hospital table itself (which serves as reference data).
    """
    rows = []
    for i in range(num_hospitals):
        country = VALID_COUNTRIES[i % len(VALID_COUNTRIES)]
        city = rng.choice(CITIES[country])
        rows.append({
            "hospitalCode": f"HOSP-{i + 1:04d}",
            "city": city,
            "country": country,
        })
    return rows


def generate_patient_summary(rng, num_patients, hospitals):
    """
    Generate Patient_Summary.csv

    Columns (from UML — Patient Identification + Hospital link):
        nationalHealthcarePatientID, familyName, givenName, dateOfBirth,
        gender, countryOfAffiliation, hospitalCode, hospitalCountry, lastUpdated

    Violations injected:
        DQR1EH — NULL nationalHealthcarePatientID at fixed indices
        DQR2EH — Invalid countryOfAffiliation at fixed indices
        DQR5EH — Gender imbalance in first half (60% M / 40% F)
        DQR6EH — Invalid hospitalCountry at fixed indices
    """
    rows = []
    violation_counts = {
        "DQR1EH_null_id": 0,
        "DQR2EH_invalid_affiliation": 0,
        "DQR5EH_male_count": 0,
        "DQR5EH_female_count": 0,
        "DQR6EH_invalid_hospital": 0,
    }

    for i in range(num_patients):
        # --- Patient ID (DQR1EH) ---
        if i in DQR1_NULL_PATIENT_INDICES:
            patient_id = ""
            violation_counts["DQR1EH_null_id"] += 1
        else:
            patient_id = f"EHDS-PT-{i + 1:05d}"

        # --- Gender (DQR5EH + DQR3EH) ---
        # First half: intentionally imbalanced (60% M / 40% F)
        # Second half: balanced (50% / 50%)
        # DQR3EH indices are forced to Male to guarantee the violation.
        half = num_patients // 2
        if i in DQR3_MALE_PREGNANCY_INDICES:
            gender = "M"  # Force male for DQR3EH violation
            rng.random()  # Consume RNG to keep sequence stable
        elif i < half:
            gender = "M" if rng.random() < 0.6 else "F"
        else:
            gender = "M" if rng.random() < 0.5 else "F"

        if gender == "M":
            violation_counts["DQR5EH_male_count"] += 1
        else:
            violation_counts["DQR5EH_female_count"] += 1

        # --- Names ---
        if gender == "M":
            given_name = rng.choice(GIVEN_NAMES_M)
        else:
            given_name = rng.choice(GIVEN_NAMES_F)
        family_name = rng.choice(FAMILY_NAMES)

        # --- Date of birth ---
        birth_year = rng.randint(1940, 2005)
        dob = f"{birth_year}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"

        # --- Country of Affiliation (DQR2EH) ---
        if i in DQR2_INVALID_AFFILIATION_INDICES:
            affiliation_country = _pick_invalid_country(
                violation_counts["DQR2EH_invalid_affiliation"]
            )
            violation_counts["DQR2EH_invalid_affiliation"] += 1
        else:
            affiliation_country = rng.choice(VALID_COUNTRIES)

        # --- Hospital assignment ---
        hospital = rng.choice(hospitals)
        hospital_code = hospital["hospitalCode"]

        # --- Hospital Country (DQR6EH) ---
        if i in DQR6_INVALID_HOSPITAL_INDICES:
            hospital_country = _pick_invalid_country(
                violation_counts["DQR6EH_invalid_hospital"]
            )
            violation_counts["DQR6EH_invalid_hospital"] += 1
        else:
            hospital_country = hospital["country"]

        # --- Timestamp ---
        last_updated = generate_timestamp(rng, 2024, 2025)

        rows.append({
            "nationalHealthcarePatientID": patient_id,
            "familyName": family_name,
            "givenName": given_name,
            "dateOfBirth": dob,
            "gender": gender,
            "countryOfAffiliation": affiliation_country,
            "hospitalCode": hospital_code,
            "hospitalCountry": hospital_country,
            "lastUpdated": last_updated,
        })

    return rows, violation_counts


def generate_pregnancy_history(rng, patients):
    """
    Generate Pregnancy_History.csv

    Columns (from UML — Pregnancy History + CurrencyPregnancyStatus):
        patientID, dateOfObservation, status, expectedDateOfDelivery

    DQR3EH violations: Males at fixed indices get pregnancy records.
    Female patients get 0–5 pregnancy records naturally.
    """
    rows = []
    male_pregnancy_count = 0

    for i, patient in enumerate(patients):
        pid = patient["nationalHealthcarePatientID"]
        if not pid:
            # Use index-based fallback for null-ID patients
            pid = f"EHDS-PT-{i + 1:05d}"

        gender = patient["gender"]

        if gender == "F":
            # Females: 0–5 pregnancies
            n_pregnancies = rng.randint(0, 5)
            for _ in range(n_pregnancies):
                obs_date = generate_date(rng, 2015, 2024)
                status = rng.choice(PREGNANCY_STATUSES)
                if status == "Delivered":
                    # Expected delivery date ~40 weeks before observation
                    edd = generate_date(rng, 2015, 2024)
                else:
                    edd = ""
                rows.append({
                    "patientID": pid,
                    "dateOfObservation": obs_date,
                    "status": status,
                    "expectedDateOfDelivery": edd,
                })

        elif i in DQR3_MALE_PREGNANCY_INDICES:
            # DQR3EH violation: male with pregnancy record
            n_pregnancies = rng.randint(1, 3)
            for _ in range(n_pregnancies):
                obs_date = generate_date(rng, 2015, 2024)
                status = rng.choice(PREGNANCY_STATUSES)
                edd = generate_date(rng, 2015, 2024) if status == "Delivered" else ""
                rows.append({
                    "patientID": pid,
                    "dateOfObservation": obs_date,
                    "status": status,
                    "expectedDateOfDelivery": edd,
                })
            male_pregnancy_count += 1

    return rows, male_pregnancy_count


def generate_allergies(rng, patients):
    """
    Generate Allergy.csv

    Columns (from UML — Allergy entity):
        patientID, allergyDescription, typeOfPropensity, allergyManifestation,
        severity, criticality, onSetDate, endDate, status, certainty,
        agentOrAllergen

    ~30% of patients have 1–3 allergies.
    """
    rows = []
    for i, patient in enumerate(patients):
        pid = patient["nationalHealthcarePatientID"]
        if not pid:
            pid = f"EHDS-PT-{i + 1:05d}"

        if rng.random() < 0.3:
            n_allergies = rng.randint(1, 3)
            for j in range(n_allergies):
                idx = rng.randint(0, len(ALLERGY_DESCRIPTIONS) - 1)
                onset = generate_date(rng, 2010, 2023)
                status = rng.choice(ALLERGY_STATUSES)
                end_date = generate_date(rng, 2023, 2025) if status == "Resolved" else ""
                rows.append({
                    "patientID": pid,
                    "allergyDescription": ALLERGY_DESCRIPTIONS[idx],
                    "typeOfPropensity": rng.choice(ALLERGY_TYPES),
                    "allergyManifestation": rng.choice(ALLERGY_MANIFESTATIONS),
                    "severity": rng.choice(ALLERGY_SEVERITIES),
                    "criticality": rng.choice(ALLERGY_CRITICALITIES),
                    "onSetDate": onset,
                    "endDate": end_date,
                    "status": status,
                    "certainty": rng.choice(["Confirmed", "Suspected", "Refuted"]),
                    "agentOrAllergen": ALLERGY_AGENTS[idx],
                })
    return rows


def generate_isolates_and_study(rng, patients, num_specimens):
    """
    Generate Isolate.csv and AMR_Study.csv

    Isolate columns (from UML):
        isolateID, patientID, laboratoryCode, date, specimen, pathogen,
        antibiotic, resistanceResult, nIsolates, resistancePercentage,
        smallSampleFlag

    AMR_Study columns (aggregate):
        studyID, description, totalIsolates, totalSpecimens, dateGenerated,
        passesDQR4EH

    DQR4EH: total isolate count must be ≥ 2000 for reliable AMR estimates.
    The generator ensures this by design.
    """
    isolate_rows = []
    total_isolates = 0

    for i in range(num_specimens):
        patient = rng.choice(patients)
        pid = patient["nationalHealthcarePatientID"]
        if not pid:
            pid = f"EHDS-PT-{rng.randint(1, len(patients)):05d}"

        organism = rng.choice(ORGANISMS)
        antibiotic = rng.choice(ANTIBIOTICS)

        # Resistance result distribution: ~50% S, ~17% I, ~33% R
        resistance_result = rng.choice(["S", "S", "S", "I", "R", "R"])

        # Number of isolates — tiered distribution
        roll = rng.random()
        if roll < 0.05:
            n_isolates = rng.randint(1, 9)       # <10: suppress
        elif roll < 0.15:
            n_isolates = rng.randint(10, 29)      # 10–29: flag
        else:
            n_isolates = rng.randint(30, 200)     # ≥30: adequate

        total_isolates += n_isolates

        # Resistance percentage
        if resistance_result == "R":
            resistance_pct = round(rng.uniform(10, 90), 1)
        elif resistance_result == "I":
            resistance_pct = round(rng.uniform(1, 10), 1)
        else:
            resistance_pct = 0.0

        # Small sample flag & suppression
        if n_isolates < 10:
            small_sample_flag = "SUPPRESS"
            resistance_pct = ""  # Suppressed per policy
        elif n_isolates < 30:
            small_sample_flag = "TRUE"
        else:
            small_sample_flag = "FALSE"

        # Laboratory code
        lab_code = f"LAB-{rng.randint(1, 100):03d}"

        isolate_rows.append({
            "isolateID": f"ISO-{i + 1:06d}",
            "patientID": pid,
            "laboratoryCode": lab_code,
            "date": generate_date(rng, 2023, 2025),
            "specimen": rng.choice(["Blood", "Urine", "Sputum", "Wound swab", "CSF", "Stool"]),
            "pathogen": organism,
            "antibiotic": antibiotic,
            "resistanceResult": resistance_result,
            "nIsolates": n_isolates,
            "resistancePercentage": resistance_pct,
            "smallSampleFlag": small_sample_flag,
        })

    # --- AMR Study aggregate ---
    passes_dqr4 = total_isolates >= 2000
    study_rows = [{
        "studyID": "EHDS-AMR-STUDY-001",
        "description": "Cross-border AMR surveillance synthetic dataset",
        "totalIsolates": total_isolates,
        "totalSpecimens": num_specimens,
        "dateGenerated": datetime.now().strftime("%Y-%m-%d"),
        "passesDQR4EH": str(passes_dqr4).upper(),
    }]

    return isolate_rows, study_rows, total_isolates, passes_dqr4


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic EHDS AMR data with deterministic DQR violations.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility (default: 42)")
    parser.add_argument("--num-patients", type=int, default=500,
                        help="Number of patients to generate (default: 500)")
    parser.add_argument("--num-specimens", type=int, default=500,
                        help="Number of AMR isolate specimens (default: 500)")
    parser.add_argument("--output-dir", type=str,
                        default=os.path.join(os.path.dirname(__file__), "..", "Data"),
                        help="Output directory for CSV files (default: ../Data)")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    output_dir = os.path.abspath(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 70)
    print("EHDS AMR Synthetic Data Generator")
    print("=" * 70)
    print(f"  Seed            : {args.seed}")
    print(f"  Num patients    : {args.num_patients}")
    print(f"  Num specimens   : {args.num_specimens}")
    print(f"  Output directory: {output_dir}")
    print()

    # 1. Hospitals (reference data)
    print("[1/5] Generating Hospital.csv ...")
    hospitals = generate_hospitals(rng, num_hospitals=50)
    checksums = {}
    checksums["Hospital.csv"] = write_csv(
        os.path.join(output_dir, "Hospital.csv"),
        ["hospitalCode", "city", "country"],
        hospitals,
    )

    # 2. Patient Summary
    print("[2/5] Generating Patient_Summary.csv ...")
    patients, patient_violations = generate_patient_summary(
        rng, args.num_patients, hospitals
    )
    checksums["Patient_Summary.csv"] = write_csv(
        os.path.join(output_dir, "Patient_Summary.csv"),
        [
            "nationalHealthcarePatientID", "familyName", "givenName",
            "dateOfBirth", "gender", "countryOfAffiliation",
            "hospitalCode", "hospitalCountry", "lastUpdated",
        ],
        patients,
    )

    # 3. Pregnancy History
    print("[3/5] Generating Pregnancy_History.csv ...")
    pregnancies, male_preg_count = generate_pregnancy_history(rng, patients)
    checksums["Pregnancy_History.csv"] = write_csv(
        os.path.join(output_dir, "Pregnancy_History.csv"),
        ["patientID", "dateOfObservation", "status", "expectedDateOfDelivery"],
        pregnancies,
    )

    # 4. Allergies
    print("[4/5] Generating Allergy.csv ...")
    allergies = generate_allergies(rng, patients)
    checksums["Allergy.csv"] = write_csv(
        os.path.join(output_dir, "Allergy.csv"),
        [
            "patientID", "allergyDescription", "typeOfPropensity",
            "allergyManifestation", "severity", "criticality",
            "onSetDate", "endDate", "status", "certainty", "agentOrAllergen",
        ],
        allergies,
    )

    # 5. Isolates & AMR Study
    print("[5/5] Generating Isolate.csv & AMR_Study.csv ...")
    isolates, study, total_isolates, passes_dqr4 = generate_isolates_and_study(
        rng, patients, args.num_specimens
    )
    checksums["Isolate.csv"] = write_csv(
        os.path.join(output_dir, "Isolate.csv"),
        [
            "isolateID", "patientID", "laboratoryCode", "date", "specimen",
            "pathogen", "antibiotic", "resistanceResult", "nIsolates",
            "resistancePercentage", "smallSampleFlag",
        ],
        isolates,
    )
    checksums["AMR_Study.csv"] = write_csv(
        os.path.join(output_dir, "AMR_Study.csv"),
        [
            "studyID", "description", "totalIsolates", "totalSpecimens",
            "dateGenerated", "passesDQR4EH",
        ],
        study,
    )

    # -----------------------------------------------------------------------
    # Verification Summary
    # -----------------------------------------------------------------------
    total_patients = args.num_patients
    male_pct = patient_violations["DQR5EH_male_count"] / total_patients * 100
    female_pct = patient_violations["DQR5EH_female_count"] / total_patients * 100

    print()
    print("=" * 70)
    print("VERIFICATION SUMMARY (Ground Truth for Paper)")
    print("=" * 70)
    print()
    print("DQR Violation Counts:")
    print(f"  DQR1EH  NULL patient IDs           : {patient_violations['DQR1EH_null_id']:>3d}  (expected: {len(DQR1_NULL_PATIENT_INDICES)})")
    print(f"  DQR2EH  Invalid affiliation country : {patient_violations['DQR2EH_invalid_affiliation']:>3d}  (expected: {len(DQR2_INVALID_AFFILIATION_INDICES)})")
    print(f"  DQR3EH  Males with pregnancy record : {male_preg_count:>3d}  (expected: {len(DQR3_MALE_PREGNANCY_INDICES)})")
    print(f"  DQR4EH  Total isolates              : {total_isolates:>5d}  (threshold: ≥ 2000, {'PASS' if passes_dqr4 else 'FAIL'})")
    print(f"  DQR5EH  Gender ratio (M/F)          : {male_pct:.1f}% / {female_pct:.1f}%  (target: 50/50)")
    print(f"  DQR6EH  Invalid hospital country    : {patient_violations['DQR6EH_invalid_hospital']:>3d}  (expected: {len(DQR6_INVALID_HOSPITAL_INDICES)})")
    print()
    print("File Checksums (MD5):")
    for fname, chk in checksums.items():
        print(f"  {fname:30s} : {chk}")
    print()
    print("Generation complete.")
    print("=" * 70)


if __name__ == "__main__":
    main()
