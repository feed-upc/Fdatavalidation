#!/usr/bin/env python3
"""
EHDS AMR Data Validation Demo — Script Version
================================================
Equivalent to demo.ipynb but runnable from the command line.

Usage:
    python run_demo.py          # Full pipeline
    python run_demo.py --skip-registration   # Skip Phase 1 (if SDM is already populated)
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from textwrap import dedent

# Add local node_modules/.bin to PATH for 'eye' reasoner
BASE_DIR = Path(__file__).resolve().parent.parent
os.environ["PATH"] = str(BASE_DIR / "node_modules/.bin") + os.pathsep + os.environ["PATH"]

# ──────────────────── helpers ────────────────────

def header(text, level=1):
    """Print a styled header."""
    if level == 1:
        print(f"\n{'='*70}")
        print(f"  {text}")
        print(f"{'='*70}\n")
    elif level == 2:
        print(f"\n{'─'*60}")
        print(f"  {text}")
        print(f"{'─'*60}\n")
    else:
        print(f"\n  ▸ {text}\n")


def run_papermill(notebook, params, label):
    """Execute a notebook via papermill and print result."""
    import papermill as pm
    print(f"  ⏳ {label} …")
    pm.execute_notebook(notebook, None, parameters=params,
                        kernel_name='python3', log_output=False)
    print(f"  ✓ {label} — done")


def run_script(cmd, cwd, label):
    """Run a Python script as a subprocess."""
    print(f"  ⏳ {label} …")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ✗ {label} FAILED")
        print(f"    stdout: {result.stdout[:500]}")
        print(f"    stderr: {result.stderr[:500]}")
        sys.exit(1)
    print(f"  ✓ {label} — done")
    return result


# ──────────────────── paths ────────────────────

BASE = str(Path(__file__).resolve().parent.parent)   # repo root

PATHS = {
    'sdm':         os.path.join(BASE, 'FederatedComputationalGovernance/SemanticDataModel/sdm.ttl'),
    'populator':   os.path.join(BASE, 'FederatedComputationalGovernance/federated_layer_populator.ipynb'),
    'profiler':    os.path.join(BASE, 'DataPlatformLayer/Registration/profiler.ipynb'),
    'federator':   os.path.join(BASE, 'DataPlatformLayer/Integration/federator.ipynb'),
    'dp1_json':    os.path.join(BASE, 'DataPlatformLayer/Integration/dp1.json'),
    'data_csv':    os.path.join(BASE, 'DataProductLayer/DataProduct_EHDS_AMR/Data/Patient_Summary.csv'),
    'planner_py':  os.path.join(BASE, 'Connector/ValidationFramework/planner/planner_n3_semantic.py'),
    'planner_dir': os.path.join(BASE, 'Connector/ValidationFramework/planner/'),
    'executor_py': os.path.join(BASE, 'Connector/ValidationFramework/executor/executor_semantic.py'),
    'executor_dir':os.path.join(BASE, 'Connector/ValidationFramework/executor/'),
    'code_meta':   os.path.join(BASE, 'Connector/ValidationFramework/executor/code_metadata_with_roles.json'),
}


# ──────────────────── PHASE 1: Federation ────────────────────

def phase1_federation():
    """Register and federate the EHDS AMR Data Product."""
    header("PHASE 1: Federation Population")

    # Step 1.1 — Initialise SDM
    header("Step 1.1  Initialise Semantic Data Model", level=2)
    run_papermill(
        PATHS['populator'],
        {'folder': os.path.join(BASE, 'FederatedComputationalGovernance/')},
        "SDM initialisation (TBox + CDM + ODRL policies)"
    )

    # Step 1.2 — Profile data product
    header("Step 1.2  Register EHDS AMR Data Product", level=2)
    print(f"  Data file: {PATHS['data_csv']}")
    run_papermill(
        PATHS['profiler'],
        {
            'folder': os.path.join(BASE, 'DataPlatformLayer/Registration'),
            'file_path': PATHS['data_csv'],
        },
        "Profiler (DCAT/CSVW metadata extraction)"
    )

    # Step 1.3 — Federate with contract
    header("Step 1.3  Create Data Contract", level=2)
    with open(PATHS['dp1_json']) as f:
        contract = json.load(f)
    print(f"  Contract: {contract['name']}")
    print(f"  Mappings: {json.dumps(contract['mappings'], indent=4)}")
    print(f"  Policies: {contract['policies']}")
    run_papermill(
        PATHS['federator'],
        {
            'folder': os.path.join(BASE, 'DataPlatformLayer/Integration'),
            'dp_meta_path': PATHS['dp1_json'],
        },
        "Federator (schema mappings + policy binding)"
    )


# ──────────────────── PHASE 1 verification ────────────────────

def verify_sdm():
    """Inspect the SDM after federation."""
    from rdflib import Graph, Namespace, RDF

    header("SDM Verification", level=2)

    sdm = Graph().parse(PATHS['sdm'], format='turtle')
    print(f"  Triples loaded: {len(sdm):,}")

    tbox = Namespace('http://www.semanticweb.org/acraf/ontologies/2024/healthmesh/tbox#')

    # Data products
    q_dp = """
    PREFIX tb: <http://www.semanticweb.org/acraf/ontologies/2024/healthmesh/tbox#>
    PREFIX csvw: <http://www.w3.org/ns/csvw#>
    SELECT ?dp (COUNT(?col) AS ?cols)
    WHERE {
        ?dp a tb:DataProduct .
        OPTIONAL { ?dp csvw:column ?col }
    }
    GROUP BY ?dp
    """
    print("\n  📊 Registered Data Products:")
    for row in sdm.query(q_dp):
        name = str(row.dp).split('#')[-1]
        print(f"     {name}  ({row.cols} columns)")

    # Policies bound
    q_pol = """
    PREFIX tb: <http://www.semanticweb.org/acraf/ontologies/2024/healthmesh/tbox#>
    SELECT ?dp ?policy
    WHERE {
        ?dp a tb:DataProduct ; tb:hasDC ?dc .
        ?dc tb:hasPolicy ?policy .
    }
    """
    print("\n  🔒 Policy Bindings:")
    for row in sdm.query(q_pol):
        dp = str(row.dp).split('#')[-1]
        pol = str(row.policy).split('#')[-1]
        print(f"     {dp} ← {pol}")

    return sdm


# ──────────────────── PHASE 2: Validation ────────────────────

def phase2_validation():
    """Run planner + executor and inspect validation results."""
    from rdflib import Graph, Namespace, RDF

    header("PHASE 2: Data Validation Workflow")

    tbox = Namespace('http://www.semanticweb.org/acraf/ontologies/2024/healthmesh/tbox#')
    abox = Namespace('http://www.semanticweb.org/acraf/ontologies/2024/healthmesh/abox#')

    # 2.1 — Discover data products
    header("Step 2.1  Discover Data Products", level=2)
    sdm = Graph().parse(PATHS['sdm'], format='turtle')

    q = """
    PREFIX tb: <http://www.semanticweb.org/acraf/ontologies/2024/healthmesh/tbox#>
    SELECT DISTINCT ?dp WHERE { ?dp a tb:DataProduct . }
    """
    data_products = sorted(set(row.dp.split('#')[1] for row in sdm.query(q)))
    print(f"  Found {len(data_products)} data product(s): {data_products}")

    # 2.2 — Planner
    header("Step 2.2  Generate PolicyCheckers (Planner)", level=2)
    for dp_name in data_products:
        run_script(
            [sys.executable, PATHS['planner_py'], PATHS['sdm'], dp_name],
            PATHS['planner_dir'],
            f"Planner → {dp_name}"
        )

    # 2.3 — Executor
    header("Step 2.3  Execute Validations (Executor)", level=2)
    sdm = Graph().parse(PATHS['sdm'], format='turtle')
    print(f"  SDM now has {len(sdm):,} triples (with PolicyCheckers)")

    # Find PolicyCheckers for Patient_Summary
    dp_uri = abox['Patient_Summary']
    policy_checkers = list(sdm.subjects(tbox.validates, dp_uri))
    print(f"  Found {len(policy_checkers)} PolicyChecker(s) for Patient_Summary\n")

    for pc_uri in policy_checkers:
        policy = sdm.value(pc_uri, tbox.accordingTo)
        policy_name = str(policy).split('#')[-1] if policy else 'Unknown'
        run_script(
            [sys.executable, PATHS['executor_py'], str(pc_uri), PATHS['code_meta']],
            PATHS['executor_dir'],
            f"Executor → policy {policy_name}"
        )


# ──────────────────── PHASE 2 verification ────────────────────

def verify_validation():
    """Query validation results from the SDM."""
    from rdflib import Graph, Namespace

    header("Validation Results", level=2)

    sdm = Graph().parse(PATHS['sdm'], format='turtle')
    print(f"  Final SDM: {len(sdm):,} triples\n")

    q = """
    PREFIX tb: <http://www.semanticweb.org/acraf/ontologies/2024/healthmesh/tbox#>
    PREFIX prov: <http://www.w3.org/ns/prov#>

    SELECT ?dataset ?policy ?status ?result ?duration
    WHERE {
        ?pc a tb:PolicyChecker ;
            tb:validates ?dataset ;
            tb:accordingTo ?policy ;
            tb:hasValidationReport ?report .
        ?report tb:validationStatus ?status .
        OPTIONAL { ?report tb:resultValue ?result }
        OPTIONAL { ?report tb:executionDuration ?duration }
    }
    ORDER BY ?dataset ?policy
    """

    rows = list(sdm.query(q))
    if not rows:
        print("  ⚠  No validation reports found in SDM.")
        print("     (This is expected if no PolicyCheckers were generated by the planner.)")
        return

    print(f"  {'Dataset':<30} {'Policy':<10} {'Status':<10} {'Result':<10} {'Duration (s)'}")
    print(f"  {'─'*80}")
    passed = failed = 0
    for row in rows:
        ds = str(row.dataset).split('#')[-1]
        pol = str(row.policy).split('#')[-1]
        st = str(row.status)
        res = str(row.result) if row.result else '—'
        dur = f"{float(row.duration):.4f}" if row.duration else '—'
        emoji = '✅' if st == 'PASSED' else '❌' if st == 'FAILED' else '⚠️'
        print(f"  {emoji} {ds:<28} {pol:<10} {st:<10} {res:<10} {dur}")
        if st == 'PASSED': passed += 1
        elif st == 'FAILED': failed += 1

    print(f"\n  Summary: {passed} passed, {failed} failed, {len(rows)} total")


# ──────────────────── main ────────────────────

def main():
    parser = argparse.ArgumentParser(description="EHDS AMR Data Validation Demo")
    parser.add_argument('--skip-registration', action='store_true',
                        help='Skip Phase 1 (SDM is already populated)')
    args = parser.parse_args()

    header("EHDS AMR Data Validation Demo")
    print(f"  Base directory: {BASE}")
    print(f"  Data product:   Patient_Summary.csv")
    print(f"  SDM:            {PATHS['sdm']}")

    # Preflight check
    missing = [k for k, v in PATHS.items() if not os.path.exists(v)]
    if missing:
        print(f"\n  ✗ Missing files: {missing}")
        sys.exit(1)
    print(f"\n  ✓ All required files present")

    # Phase 1
    if not args.skip_registration:
        phase1_federation()
        verify_sdm()
    else:
        print("\n  ⏭  Skipping Phase 1 (--skip-registration)")

    # Phase 2
    phase2_validation()
    verify_validation()

    header("Demo Complete 🎉")


if __name__ == '__main__':
    main()
