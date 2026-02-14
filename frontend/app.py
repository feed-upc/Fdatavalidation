#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import glob
from pathlib import Path
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
import papermill as pm
from rdflib import Graph, Namespace, Literal, URIRef

app = Flask(__name__)
CORS(app)

# ──────────────────── Configuration ────────────────────

BASE = str(Path(__file__).resolve().parent.parent)
# Add node_modules/.bin to PATH for 'eye'
os.environ["PATH"] = str(Path(BASE) / "node_modules/.bin") + os.pathsep + os.environ["PATH"]

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

# ──────────────────── Helpers ────────────────────

def run_papermill_notebook(notebook_path, params):
    """Run a notebook using papermill."""
    try:
        pm.execute_notebook(
            notebook_path,
            None,
            parameters=params,
            kernel_name='python3',
            log_output=True # Log to stderr/stdout
        )
        return True, "Notebook executed successfully"
    except Exception as e:
        return False, str(e)

def run_python_script(cmd, cwd):
    """Run a python script as subprocess."""
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
             return False, result.stderr + "\n" + result.stdout
        return True, result.stdout
    except Exception as e:
        return False, str(e)

def get_graph_data(mode='full'):
    """Parse SDM and return nodes/edges for visualization."""
    if not os.path.exists(PATHS['sdm']):
        return {'elements': {'nodes': [], 'edges': []}}
    
    g = Graph()
    try:
        g.parse(PATHS['sdm'], format='turtle')
    except Exception as e:
        return {'error': str(e)}

    nodes = []
    edges = []
    
    added_nodes = set()
    
    # helper for label
    def get_label(uri):
        if '#' in uri:
            return uri.split('#')[-1]
        return uri.split('/')[-1]

    # Namespaces to filter out in simple mode
    FILTER_PREFIXES = [
        "http://www.w3.org/1999/02/22-rdf-syntax-ns#", # rdf
        "http://www.w3.org/2000/01/rdf-schema#",       # rdfs
        "http://www.w3.org/2002/07/owl#",              # owl
        "http://www.w3.org/ns/prov#",                  # prov (optional, keep if needed)
    ]
    
    # Predicates to KEEP in simple mode
    # We want to see the workflow flow
    IMPORTANT_PREDICATES = [
        "http://www.semanticweb.org/acraf/ontologies/2024/healthmesh/tbox#validates",
        "http://www.semanticweb.org/acraf/ontologies/2024/healthmesh/tbox#accordingTo",
        "http://www.semanticweb.org/acraf/ontologies/2024/healthmesh/tbox#nextStep",
        "http://www.semanticweb.org/acraf/ontologies/2024/healthmesh/tbox#hasInput",
        "http://www.semanticweb.org/acraf/ontologies/2024/healthmesh/tbox#hasOutput",
        "http://www.semanticweb.org/acraf/ontologies/2024/healthmesh/tbox#hasPolicy",
        "http://www.w3.org/ns/odrl/2/target",
        "http://www.w3.org/ns/odrl/2/partOf"
    ]

    for s, p, o in g:
        s_id = str(s)
        p_id = str(p)
        o_id = str(o)
        
        # ─── SIMPLE MODE FILTERING ───
        if mode == 'simple':
            # 1. Hide Literals entirely
            if not isinstance(o, URIRef):
                continue
            
            # 2. Hide specific "noisy" predicates unless they are critical
            #    (e.g. hide rdf:type unless it's a key entity type we want - but usually clutter)
            if p_id not in IMPORTANT_PREDICATES:
                # Optional: Allow rdf:type for key classes if desired, but for now strict filter
                # to show only connections between instances
                continue

        # ─── NODE GENERATION ───

        # Add Node S
        if s_id not in added_nodes:
            label = get_label(s_id)
            nodes.append({'data': {'id': s_id, 'label': label, 'type': 'resource'}})
            added_nodes.add(s_id)
            
        # Add Node O
        if isinstance(o, URIRef):
             if o_id not in added_nodes:
                label = get_label(o_id)
                nodes.append({'data': {'id': o_id, 'label': label, 'type': 'resource'}})
                added_nodes.add(o_id)
        else:
             # Literal node (only implies mode='full' here due to check above)
             import hashlib
             lit_hash = hashlib.md5(f"{s_id}_{p_id}_{o_id}".encode()).hexdigest()
             lit_id = f"lit_{lit_hash}"
             
             if lit_id not in added_nodes:
                 nodes.append({'data': {'id': lit_id, 'label': str(o), 'type': 'literal'}})
                 added_nodes.add(lit_id)
             o_id = lit_id

        # ─── EDGE GENERATION ───
        import hashlib
        edge_hash = hashlib.md5(f"{s_id}_{p_id}_{o_id}".encode()).hexdigest()
        edge_id = f"edge_{edge_hash}"
        
        edge_label = get_label(p_id)
        edges.append({'data': {'id': edge_id, 'source': s_id, 'target': o_id, 'label': edge_label}})

    return {'elements': {'nodes': nodes, 'edges': edges}}


# ──────────────────── Routes ────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/step1_init', methods=['POST'])
def step1_init():
    """Step 1.1: Initialize SDM"""
    success, msg = run_papermill_notebook(
        PATHS['populator'],
        {'folder': os.path.join(BASE, 'FederatedComputationalGovernance/')}
    )
    if success:
        return jsonify({'status': 'success', 'message': 'SDM Initialized (TBox + CDM + Policies)'})
    return jsonify({'status': 'error', 'message': str(msg)}), 500

@app.route('/api/step2_register', methods=['POST'])
def step2_register():
    """Step 1.2: Register Data Product (Profiler)"""
    success, msg = run_papermill_notebook(
         PATHS['profiler'],
        {
            'folder': os.path.join(BASE, 'DataPlatformLayer/Registration'),
            'file_path': PATHS['data_csv'],
        }
    )
    if success:
        return jsonify({'status': 'success', 'message': 'Data Product Registered (Profiler executed)'})
    return jsonify({'status': 'error', 'message': str(msg)}), 500

@app.route('/api/step3_contract', methods=['POST'])
def step3_contract():
    """Step 1.3: Create Data Contract (Federator)"""
    success, msg = run_papermill_notebook(
        PATHS['federator'],
        {
            'folder': os.path.join(BASE, 'DataPlatformLayer/Integration'),
            'dp_meta_path': PATHS['dp1_json'],
        }
    )
    if success:
        return jsonify({'status': 'success', 'message': 'Data Contract Created (Federator executed)'})
    return jsonify({'status': 'error', 'message': str(msg)}), 500

@app.route('/api/step4_validate', methods=['POST'])
def step4_validate():
    """Step 2: Validation (Planner + Executor)"""
    
    # 2.1 Discover products
    dp_name = "Patient_Summary" # Simplified
    
    # 2.2 Planner
    cmd_planner = [sys.executable, PATHS['planner_py'], PATHS['sdm'], dp_name]
    success_p, msg_p = run_python_script(cmd_planner, PATHS['planner_dir'])
    if not success_p:
         return jsonify({'status': 'error', 'message': 'Planner Failed: ' + str(msg_p)}), 500

    # 2.3 Executor
    g = Graph()
    g.parse(PATHS['sdm'], format='turtle')
    tbox = Namespace('http://www.semanticweb.org/acraf/ontologies/2024/healthmesh/tbox#')
    abox = Namespace('http://www.semanticweb.org/acraf/ontologies/2024/healthmesh/abox#')
    dp_uri = abox['Patient_Summary']
    
    policy_checkers = list(g.subjects(tbox.validates, dp_uri))
    if not policy_checkers:
        return jsonify({'status': 'warning', 'message': 'Planner finished but no PolicyCheckers found.'})
    
    executor_logs = []
    
    for pc_uri in policy_checkers:
        policy = g.value(pc_uri, tbox.accordingTo)
        policy_name = str(policy).split('#')[-1] if policy else 'Unknown'
        
        cmd_exec = [sys.executable, PATHS['executor_py'], str(pc_uri), PATHS['code_meta']]
        success_e, msg_e = run_python_script(cmd_exec, PATHS['executor_dir'])
        
        status = "Success" if success_e else "Failed"
        executor_logs.append({'policy': policy_name, 'status': status, 'details': msg_e})

    return jsonify({
        'status': 'success', 
        'message': 'Validation Complete', 
        'planner_log': msg_p, 
        'executor_logs': executor_logs
    })

@app.route('/api/graph', methods=['GET'])
def get_graph():
    mode = request.args.get('mode', 'full')
    data = get_graph_data(mode=mode)
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
