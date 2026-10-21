"""Synthetic data for the HELEADE wetlands data product.

Generates every entity of the HELEADE data model (Metadata/UML.png):

  Wetland                    -> wetland.csv
  MonitoringSite             -> monitoring_site.csv
  Species                    -> species.csv
  WaterLevelSeries           -> water_level_series.csv
  WaterManagementOperation   -> water_management_operation.csv
  Observation, with its three subclasses WaterLevelObservation, WeatherObservation
  and BiodiversityObservation in one table told apart by observationType
                             -> observation.csv

The three wetlands are the real ones of southern Alicante; everything else is
generated. Wetlands, sites and observations are drawn exactly as the DQVP pipeline's
generator draws them (tools/dqvp/data/heleade/generate.py, same seed), so the first
eight columns of observation.csv and the whole of wetland.csv and monitoring_site.csv
equal the data the DQVP pipeline validates. The remaining attributes come from a second
random stream and do not change those rows.

Each quality defect is a switch, as in the DQVP generator:

  missing_location   one monitoring site has no location            (DQR1HL)
  non_utc            five observation timestamps are not UTC        (DQR2HL)
  breeding_conflict  three 'notDetected' records report breeding    (DQR3HL)
  thin_wetland       one wetland has only four monitoring sites     (DQR4HL)

The default dataset turns on non_utc and thin_wetland, so DQR2HL and DQR4HL are
violated and DQR1HL and DQR3HL are satisfied.

Usage:
    python generate_synthetic_data.py [--seed 7] [--output-dir Data] [--clean | --all-defects]
"""
import argparse
import csv
import hashlib
import random
from pathlib import Path

WETLANDS = [("WL-HONDO", "El Hondo"),
            ("WL-SPOLA", "Salinas de Santa Pola"),
            ("WL-MATA", "Lagunas de La Mata y Torrevieja")]
CENTRE = {"WL-HONDO": (38.27, -0.70), "WL-SPOLA": (38.18, -0.62), "WL-MATA": (38.03, -0.70)}
SPECIES = [("SP-01", "Marmaronetta angustirostris"),
           ("SP-02", "Phoenicopterus roseus"),
           ("SP-03", "Himantopus himantopus")]
TAXA = [name for _, name in SPECIES]
TAXON_ID = {name: tid for tid, name in SPECIES}
BREEDING = ["courtship", "nesting", "chicks"]
OBSERVATIONS_PER_SITE = 30

# Who changes the water level of each wetland: irrigation communities at El Hondo,
# salt producers at Santa Pola and La Mata, and the water-management company.
OPERATIONS = [
    ("WL-HONDO", "OP-IRRIGATION-01", "waterIntake",   "2026-04-24T06:00:00Z", "2026-04-26T18:00:00Z"),
    ("WL-HONDO", "OP-IRRIGATION-01", "waterRelease",  "2026-04-08T08:00:00Z", "2026-04-08T20:00:00Z"),
    ("WL-HONDO", "OP-WATER-01",      "waterTransfer", "2026-04-15T07:00:00Z", "2026-04-16T07:00:00Z"),
    ("WL-SPOLA", "OP-SALT-01",       "waterIntake",   "2026-04-05T05:00:00Z", "2026-04-07T05:00:00Z"),
    ("WL-SPOLA", "OP-SALT-01",       "waterRelease",  "2026-04-20T09:00:00Z", "2026-04-21T09:00:00Z"),
    ("WL-MATA",  "OP-SALT-02",       "waterIntake",   "2026-04-10T06:00:00Z", "2026-04-12T06:00:00Z"),
    ("WL-MATA",  "OP-WATER-01",      "waterTransfer", "2026-04-27T07:00:00Z", "2026-04-28T19:00:00Z"),
]

SHIPPED = {"non_utc", "thin_wetland"}
ALL = {"missing_location", "non_utc", "breeding_conflict", "thin_wetland"}


def write(path, header, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def generate(out_dir, defects=SHIPPED, seed=7):
    rng = random.Random(seed)            # the DQVP generator's stream: do not add draws to it
    extra = random.Random(seed + 1)      # everything the DQVP generator does not draw
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    write(out / "wetland.csv", ["wetlandId", "name"], WETLANDS)

    per_wetland = {"WL-HONDO": 7, "WL-SPOLA": 6,
                   "WL-MATA": 4 if "thin_wetland" in defects else 5}
    sites = []
    for wid, n in per_wetland.items():
        lat, lon = CENTRE[wid]
        for i in range(1, n + 1):
            point = f"POINT({lon + rng.uniform(-.03, .03):.5f} {lat + rng.uniform(-.03, .03):.5f})"
            sites.append([f"{wid}-S{i}", f"{wid} site {i}", point, wid])
    if "missing_location" in defects:
        sites[3][2] = ""
    write(out / "monitoring_site.csv", ["siteId", "name", "location", "wetlandId"], sites)

    write(out / "species.csv", ["taxonId", "scientificName"], SPECIES)

    # One hourly water-level series per site over the observation period.
    series = [[f"{s[0]}-WLS", s[0], "2026-04-01T00:00:00Z", "2026-04-30T23:00:00Z", 60] for s in sites]
    write(out / "water_level_series.csv",
          ["seriesId", "siteId", "periodStartUTC", "periodEndUTC", "intervalMinutes"], series)

    write(out / "water_management_operation.csv",
          ["operationId", "wetlandId", "operatorId", "operationType", "plannedStart", "plannedEnd"],
          [[f"OPR-{i:03d}", *op] for i, op in enumerate(OPERATIONS, 1)])

    rows = []
    for site in sites:
        for k in range(OBSERVATIONS_PER_SITE):
            kind = ("waterLevel", "weather", "biodiversity")[k % 3]
            observed = f"2026-04-{1 + k % 28:02d}T{(6 + k) % 24:02d}:00:00Z"
            level = status = breeding = taxon = ""
            series_id = unit = temp = rain = wind = count = taxon_id = ""
            if kind == "waterLevel":
                level = f"{rng.uniform(0.2, 1.4):.2f}"
                series_id, unit = f"{site[0]}-WLS", "m"
            if kind == "weather":
                temp = f"{extra.uniform(11.0, 27.0):.1f}"
                rain = f"{extra.choice([0.0, 0.0, 0.0, extra.uniform(0.2, 12.0)]):.1f}"
                wind = f"{extra.uniform(0.5, 11.0):.1f}"
            if kind == "biodiversity":
                status = rng.choice(["detected", "notDetected"])
                breeding = rng.choice(BREEDING + [""]) if status == "detected" else ""
                taxon = rng.choice(TAXA)
                taxon_id = TAXON_ID[taxon]
                count = str(extra.randint(1, 40)) if status == "detected" else ""
            rows.append([f"OBS-{len(rows) + 1:05d}", site[0], observed, kind,
                         level, status, breeding, taxon,
                         series_id, unit, temp, rain, wind, count, taxon_id])
    if "non_utc" in defects:
        for i in (10, 200, 333, 410):                 # local time with an offset
            rows[i][2] = rows[i][2].replace("Z", "+02:00")
        rows[500][2] = rows[500][2].replace("T", " ").replace("Z", "")   # no zone
    if "breeding_conflict" in defects:
        conflicting = [r for r in rows if r[5] == "notDetected"][:3]
        for r, evidence in zip(conflicting, BREEDING):
            r[6] = evidence
    write(out / "observation.csv",
          ["observationId", "siteId", "observedAt", "observationType",
           "waterLevel", "detectionStatus", "breedingEvidence", "taxon",
           "seriesId", "unit", "airTemperature", "precipitation", "windSpeed",
           "individualCount", "taxonId"], rows)
    return sites, rows


def summary(out_dir, defects, sites, rows):
    """What a reader checks first: each DQR's defect, and a checksum per file."""
    per = {}
    for s in sites:
        per[s[3]] = per.get(s[3], 0) + 1
    not_utc = [r[0] for r in rows if not r[2].endswith("Z")]
    nd = [r for r in rows if r[5] == "notDetected"]
    print(f"defects: {', '.join(sorted(defects)) or 'none'}")
    print(f"  DQR1HL  sites without location: {sum(1 for s in sites if not s[2])} of {len(sites)}")
    print(f"  DQR2HL  observations not in UTC: {len(not_utc)} of {len(rows)} {not_utc}")
    print(f"  DQR3HL  notDetected with breeding evidence: {sum(1 for r in nd if r[6])} of {len(nd)}")
    print(f"  DQR4HL  sites per wetland: {per}")
    for f in sorted(Path(out_dir).glob("*.csv")):
        print(f"  {hashlib.md5(f.read_bytes()).hexdigest()}  {f.name}")


if __name__ == "__main__":
    here = Path(__file__).resolve().parent.parent
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--seed", type=int, default=7, help="random seed (default: 7)")
    p.add_argument("--output-dir", default=str(here / "Data"), help="output folder (default: Data/)")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--clean", action="store_true", help="no defects: every DQR is satisfied")
    g.add_argument("--all-defects", action="store_true", help="every defect: every DQR is violated")
    a = p.parse_args()
    defects = set() if a.clean else ALL if a.all_defects else SHIPPED
    sites, rows = generate(a.output_dir, defects, a.seed)
    summary(a.output_dir, defects, sites, rows)
