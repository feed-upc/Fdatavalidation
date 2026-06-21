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
        print(f"    stdout: {result.stdout}")
        print(f"    stderr: {result.stderr}")
        sys.exit(1)
    # Show key executor debug lines
    for line in result.stdout.split('\n'):
        if any(k in line for k in ['Step ', 'GX Type:', 'COMPOSING', 'Merged']):
            print(f"    {line.strip()}")
    print(f"  ✓ {label} — done")
    return result.stdout


# ──────────────────── paths ────────────────────

BASE = str(Path(__file__).resolve().parent.parent)   # repo root

PATHS = {
    'sdm':         os.path.join(BASE, 'FederatedComputationalGovernance/SemanticDataModel/sdm.ttl'),
    'populator':   os.path.join(BASE, 'FederatedComputationalGovernance/federated_layer_populator.ipynb'),
    'profiler':    os.path.join(BASE, 'DataPlatformLayer/Registration/profiler.ipynb'),
    'federator':   os.path.join(BASE, 'DataPlatformLayer/Integration/federator.ipynb'),
    'dp1_json':    os.path.join(BASE, 'DataPlatformLayer/Integration/dp1.json'),
    'data_csv':    os.path.join(BASE, 'DataProductLayer/DataProduct_EHDS_AMR/Data/Patient_Summary.csv'),
    'planner_py':  os.path.join(BASE, 'Connector/ValidationFramework/planner/planner.py'),
    'planner_dir': os.path.join(BASE, 'Connector/ValidationFramework/planner/'),
    'executor_py': os.path.join(BASE, 'Connector/ValidationFramework/executor/executor.py'),
    'executor_dir':os.path.join(BASE, 'Connector/ValidationFramework/executor/'),
    'code_meta':   os.path.join(BASE, 'Connector/ValidationFramework/executor/code_metadata.json'),
}


# ──────────────────── policy injection ────────────────────

def _remove_op_chain(sdm, op_uri, tbox):
    """Recursively remove an operation and its chain from the SDM."""
    if op_uri is None:
        return
    next_op = sdm.value(op_uri, tbox.nextStep)
    for t in list(sdm.triples((op_uri, None, None))):
        sdm.remove(t)
    for t in list(sdm.triples((None, None, op_uri))):
        sdm.remove(t)
    _remove_op_chain(sdm, next_op, tbox)


def inject_policies_into_sdm():
    """
    When --skip-registration is used, the SDM may not contain the requested policy.
    Read dp1.json to find which policies are needed, load their ODRL JSON-LD into
    the SDM, and replace existing policy bindings on the data contract.
    Also ensures attribute triples and schema mappings exist for dp1.json mappings.
    """
    import uuid
    from rdflib import Graph, Namespace, Literal, RDF, URIRef

    tbox = Namespace('http://www.semanticweb.org/acraf/ontologies/2024/healthmesh/tbox#')
    abox = Namespace('http://www.semanticweb.org/acraf/ontologies/2024/healthmesh/abox#')
    csvw = Namespace('http://www.w3.org/ns/csvw#')
    SCHEMA = Namespace('http://schema.org/')

    header("Injecting Requested Policies into SDM", level=2)

    with open(PATHS['dp1_json']) as f:
        contract = json.load(f)

    requested_policies = contract.get('policies', [])
    if not requested_policies:
        print("  No policies in dp1.json — nothing to inject.")
        return

    sdm = Graph().parse(PATHS['sdm'], format='turtle')
    initial = len(sdm)
    print(f"  SDM has {initial:,} triples")
    print(f"  Requested policies: {requested_policies}")

    # Find or create the data product
    dp_name = contract.get('name', 'Patient_Summary')
    dp_uri = abox[dp_name]

    # If the data product doesn't exist in the SDM, create it dynamically
    if (dp_uri, RDF.type, tbox.DataProduct) not in sdm:
        DCAT = Namespace('http://www.w3.org/ns/dcat#')
        DCT  = Namespace('http://purl.org/dc/terms/')
        RDFS = Namespace('http://www.w3.org/2000/01/rdf-schema#')

        # Derive the data file path by convention — search all DataProduct_* dirs
        data_path = None
        dp_base = os.path.join(BASE, 'DataProductLayer')
        for entry in os.listdir(dp_base):
            candidate = os.path.join(dp_base, entry, 'Data', f'{dp_name}.csv')
            if os.path.exists(candidate):
                data_path = candidate
                break
        if not data_path:
            print(f"  ⚠ Cannot create data product '{dp_name}': CSV not found in DataProductLayer/*/Data/")
            return

        ta_uri     = abox[f'{dp_name}_TA']
        access_uri = abox[f'{dp_name}_Acces']
        dc_uri     = abox[f'dc_{dp_name}']

        # DataProduct node
        sdm.add((dp_uri, RDF.type, tbox.DataProduct))
        sdm.add((dp_uri, RDF.type, DCAT.Dataset))
        sdm.add((dp_uri, DCT.title, Literal(f'{dp_name} Dataset')))
        sdm.add((dp_uri, tbox.hasDTT, abox.Tabular))

        # TechnologyAspects / Distribution
        sdm.add((dp_uri, tbox.hasTA, ta_uri))
        sdm.add((dp_uri, DCAT.distribution, ta_uri))
        sdm.add((ta_uri, RDF.type, tbox.TechnologyAspects))
        sdm.add((ta_uri, RDF.type, DCAT.Distribution))
        sdm.add((ta_uri, DCT['format'], Literal('CSV')))
        sdm.add((ta_uri, DCAT.mediaType, Literal('text/csv')))
        sdm.add((ta_uri, DCAT.accessURL, URIRef(f'file://{data_path}')))

        # Access node (Static file access)
        sdm.add((ta_uri, tbox.hasAcces, access_uri))
        sdm.add((access_uri, RDF.type, tbox.Acces))
        sdm.add((access_uri, RDFS.label, abox.Static))
        sdm.add((access_uri, tbox.path, Literal(data_path)))

        # DataContract
        sdm.add((dp_uri, tbox.hasDC, dc_uri))
        sdm.add((dc_uri, RDF.type, tbox.DataContract))
        sdm.add((dc_uri, RDF.type, URIRef('http://www.w3.org/ns/odrl/2/Agreement')))

        print(f"  + Created data product '{dp_name}' with TA → Access({data_path}) → DC")

    dc = sdm.value(dp_uri, tbox.hasDC)
    if not dc:
        print(f"  ⚠ No data contract found for {dp_name}")
        return

    # Remove ALL existing policy bindings from the data contract
    old_policies = list(sdm.objects(dc, tbox.hasPolicy))
    for old_p in old_policies:
        sdm.remove((dc, tbox.hasPolicy, old_p))
        label = str(old_p).split('#')[-1] if '#' in str(old_p) else str(old_p)
        print(f"  - Removed stale binding: {label}")

    # Remove stale PolicyChecker triples (from previous planner runs)
    checkers = list(sdm.subjects(tbox.validates, dp_uri))
    removed_count = 0
    for checker in checkers:
        # Remove operation chain first
        first_op = sdm.value(checker, tbox.nextStep)
        _remove_op_chain(sdm, first_op, tbox)
        # Remove all triples where checker is subject or object
        for t in list(sdm.triples((checker, None, None))):
            sdm.remove(t)
        for t in list(sdm.triples((None, None, checker))):
            sdm.remove(t)
        removed_count += 1
    if removed_count:
        print(f"  - Removed {removed_count} stale PolicyChecker(s) and their operations")

    # ── Ensure attribute triples and schema mappings exist for dp1.json mappings ──
    mappings = contract.get('mappings', {})
    for physical, semantic in mappings.items():
        phys_uri = abox[physical]
        sem_uri = abox[semantic]

        # Check if physical column has Attribute type
        if (phys_uri, RDF.type, tbox.Attribute) not in sdm:
            sdm.add((phys_uri, RDF.type, tbox.Attribute))
            sdm.add((phys_uri, RDF.type, csvw.Column))
            sdm.add((phys_uri, tbox.attribute, Literal(physical)))
            sdm.add((phys_uri, tbox.semanticFeature, Literal(semantic)))
            sdm.add((phys_uri, csvw.datatype, Literal("string")))
            sdm.add((phys_uri, csvw['name'], Literal(physical)))
            sdm.add((phys_uri, csvw.propertyUrl, SCHEMA.propertyValue))
            # Link to dataset
            sdm.add((dp_uri, tbox.hasAttribute, phys_uri))
            sdm.add((dp_uri, csvw.column, phys_uri))
            print(f"  + Created attribute triples for {physical}")

        # Check if a SchemaMapping mfrom→mto already exists
        has_mapping = False
        for mapping_node in sdm.subjects(RDF.type, tbox.SchemaMapping):
            mfrom = sdm.value(mapping_node, tbox.mfrom)
            mto = sdm.value(mapping_node, tbox.mto)
            if mfrom == phys_uri and mto == sem_uri:
                has_mapping = True
                break

        if not has_mapping:
            mapping_uri = abox[str(uuid.uuid4())]
            sdm.add((mapping_uri, RDF.type, tbox.SchemaMapping))
            sdm.add((mapping_uri, tbox.mfrom, phys_uri))
            sdm.add((mapping_uri, tbox.mto, sem_uri))
            sdm.add((dc, tbox.hasMapping, mapping_uri))
            print(f"  + Created mapping {physical} → {semantic}")

    # ── Load ODRL policies ──
    odrl_dir = Path(BASE) / 'FederatedComputationalGovernance' / 'ComputationalCatalogues' / 'prototype' / 'odrl_rules'

    for policy_name in requested_policies:
        policy_uri = abox[policy_name]

        # Check if ODRL triples already in SDM
        if (policy_uri, RDF.type, None) in sdm:
            print(f"  ✓ {policy_name} ODRL already in SDM")
        else:
            # Try to find the ODRL JSON-LD file
            # Convention: {dqr_id}_odrl.json  where policy_name = "{dqr_id}Rule"
            dqr_id = policy_name.replace('Rule', '')
            candidates = [
                odrl_dir / f"{dqr_id}_odrl.json",
            ]

            loaded = False
            for candidate in candidates:
                if candidate.exists():
                    with open(candidate) as f:
                        odrl_data = json.load(f)
                    sdm.parse(data=json.dumps(odrl_data), format='json-ld')
                    print(f"  + Loaded {policy_name} from {candidate.name}")
                    loaded = True
                    break

            if not loaded:
                print(f"  ⚠ Could not find ODRL file for {policy_name}")
                continue

        # Bind to the data contract
        sdm.add((dc, tbox.hasPolicy, policy_uri))
        print(f"  + Bound {policy_name} to data contract")

    final = len(sdm)
    sdm.serialize(PATHS['sdm'], format='turtle')
    print(f"  ✓ SDM updated: {initial:,} → {final:,} triples (saved)")


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

def phase2_validation(export_docker_dir=None, backend="pandas"):
    """Run planner + executor and inspect validation results."""
    from rdflib import Graph, Namespace, RDF

    header(f"PHASE 2: Data Validation Workflow (Backend: {backend.upper()})")

    tbox = Namespace('http://www.semanticweb.org/acraf/ontologies/2024/healthmesh/tbox#')
    abox = Namespace('http://www.semanticweb.org/acraf/ontologies/2024/healthmesh/abox#')
    
    metadata_file = PATHS['code_meta']
    if backend == 'gx':
        metadata_file = os.path.join(os.path.dirname(PATHS['code_meta']), 'gx_metadata.json')

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

    # Find PolicyCheckers for all data products
    total_checkers = 0
    for dp_name in data_products:
        dp_uri = abox[dp_name]
        policy_checkers = list(sdm.subjects(tbox.validates, dp_uri))
        if not policy_checkers:
            continue
        print(f"  Found {len(policy_checkers)} PolicyChecker(s) for {dp_name}")
        total_checkers += len(policy_checkers)

        for pc_uri in policy_checkers:
            policy = sdm.value(pc_uri, tbox.accordingTo)
            policy_name = str(policy).split('#')[-1] if policy else 'Unknown'
            
            cmd = [sys.executable, PATHS['executor_py'], str(pc_uri), metadata_file]
            if export_docker_dir:
                cmd.append(f"--export-docker={os.path.abspath(export_docker_dir)}")
            
            if backend:
                cmd.append(f"--backend={backend}")
                
            run_script(
                cmd,
                PATHS['executor_dir'],
                f"Executor → policy {policy_name}"
            )

    if total_checkers == 0:
        print("  ⚠ No PolicyCheckers found for any data product")


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


def test_docker_exports(export_dir):
    """Build and run the exported Dockerized validation services natively."""
    import shutil
    header("PHASE 3: Dockerized Service Testing")
    
    docker_cmd = shutil.which("docker") or shutil.which("docker.exe")
    if not docker_cmd:
        print("  ⚠ Docker command not found. Please install Docker or enable WSL integration.")
        return

    if not os.path.exists(export_dir):
        print(f"  ⚠ Export directory not found: {export_dir}")
        return
        
    services = [d for d in os.listdir(export_dir) if d.startswith("policyChecker_")]
    if not services:
        print(f"  ⚠ No 'policyChecker_' services found in {export_dir}")
        return
        
    print(f"  Found {len(services)} exported Docker services. Testing...")
    
    # Needs absolute path for docker volume mount
    data_file_abs = os.path.abspath(PATHS['data_csv'])
    data_dir_abs = os.path.dirname(data_file_abs)
    data_filename = os.path.basename(data_file_abs)
    
    passed = 0
    failed = 0
    
    for service_name in services:
        service_path = os.path.join(export_dir, service_name)
        # Docker image names must be lowercased
        image_name = service_name.lower()
        
        print(f"\n  {'─'*60}")
        print(f"  Testing Service: {service_name}")
        print(f"  {'─'*60}")
        
        # 1. Build Docker image
        print(f"  ⏳ Building Docker image '{image_name}' ...")
        build_cmd = [docker_cmd, "build", "-t", image_name, "."]
        build_res = subprocess.run(build_cmd, cwd=service_path, capture_output=True, text=True)
        
        if build_res.returncode != 0:
            print(f"  ✗ Build FAILED")
            print(f"    {build_res.stderr.strip().split(chr(10))[-1]}")
            failed += 1
            continue
            
        print(f"  ✓ Build successful")
        
        # 2. Run Docker container mapped to the data file
        print(f"  ⏳ Running container locally against {data_filename} ...")
        run_cmd = [
            docker_cmd, "run", "--rm",
            "-v", f"{data_dir_abs}:/data",
            image_name,
            f"/data/{data_filename}"
        ]
        run_res = subprocess.run(run_cmd, capture_output=True, text=True)
        
        if run_res.returncode != 0:
            print(f"  ✗ Execution FAILED")
            print(f"    {run_res.stderr.strip().split(chr(10))[-1]}")
            failed += 1
        else:
            print(f"  ✓ Execution successful")
            # Extract just the result section to show
            output_lines = run_res.stdout.split('\n')
            result_idx = -1
            for i, line in enumerate(output_lines):
                if "=== VALIDATION RESULT ===" in line:
                    result_idx = i + 1
                    break
            
            if result_idx != -1 and result_idx < len(output_lines):
                res_val = output_lines[result_idx].strip()
                print(f"  Result: {res_val}")
            passed += 1

    print(f"\n  Summary: {passed} passed, {failed} failed, {len(services)} total Docker tests")


# ──────────────────── main ────────────────────

def main():
    parser = argparse.ArgumentParser(description="EHDS AMR Data Validation Demo")
    parser.add_argument('--skip-registration', action='store_true',
                        help='Skip Phase 1 (SDM is already populated)')
    parser.add_argument('--export-docker', type=str, metavar='DIR',
                        help='Export standalone Docker validation services to DIR')
    parser.add_argument('--test-docker-exports', action='store_true',
                        help='Build and run exported Docker services natively to test them')
    parser.add_argument('--backend', type=str, choices=['pandas', 'gx'], default='pandas',
                        help='Execution backend to use (pandas or gx)')
    parser.add_argument('--dp-contract', type=str, metavar='PATH',
                        help='Path to data product contract JSON (default: dp1.json)')
    args = parser.parse_args()

    # Override dp1_json path if a custom contract was specified
    if args.dp_contract:
        PATHS['dp1_json'] = args.dp_contract

    header("EHDS AMR Data Validation Demo")
    print(f"  Base directory: {BASE}")
    with open(PATHS['dp1_json']) as _f:
        _contract = json.load(_f)
    print(f"  Data product:   {_contract.get('name', 'Patient_Summary')}.csv")
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
        # Inject requested policies into the SDM so Phase 2 can find them
        inject_policies_into_sdm()

    # Phase 2
    phase2_validation(export_docker_dir=args.export_docker, backend=args.backend)
    verify_validation()
    
    # Phase 3 (Optional Docker Testing)
    if args.export_docker and args.test_docker_exports:
        test_docker_exports(args.export_docker)

    header("Demo Complete 🎉")


if __name__ == '__main__':
    main()
