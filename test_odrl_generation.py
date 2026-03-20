"""
End-to-end test for ODRL rule generation from requirements + templates.
Verifies that build_odrl_rule produces correct output for all 6 DQR*EH requirements
and cross-checks against the existing saved ODRL rules and what the N3 planner expects.
"""
import json
import sys
import os
from pathlib import Path

# Add prototype dir to path for imports
PROTO_DIR = Path("FederatedComputationalGovernance/ComputationalCatalogues/prototype")
REQUIREMENTS_DIR = PROTO_DIR / "requirements"
TEMPLATES_DIR = PROTO_DIR / "odrl_templates"
RULES_DIR = PROTO_DIR / "odrl_rules"
PATTERNS_DIR = PROTO_DIR / "patterns"

# ========== Inline build_odrl_rule from dqr_prototype_gui.py ==========
# (we can't import from streamlit app directly)

def build_odrl_rule(requirement, template):
    params = requirement.get("parameters", {})
    constraint_tmpl = template["constraint"]
    attribute = params.get(template["target"]["parameter"])
    req_id = requirement["id"]
    dim = requirement["qualityDimension"]["dimension"]
    concept = requirement.get("measurementConcept", dim)

    # --- Refinement-based template (DQRP4: Consistency) ---
    if "refinement" in template:
        ref_tmpl = template["refinement"]

        def clean_valueset(v):
            return ','.join(s.strip() for s in str(v).strip('{}').split(','))

        ref_attr = params.get(ref_tmpl["leftOperand"]["parameter"])
        ref_values = clean_valueset(params.get(ref_tmpl["rightOperand"]["parameter"], ""))
        ref_operator = ref_tmpl["operator"]

        con_operator = constraint_tmpl["operator"]
        expected_value = clean_valueset(params.get(constraint_tmpl["rightOperand"]["parameter"], ""))

        refinement_block = {
            "@id": f"ab:{req_id}_Refinement",
            "@type": "odrl:Constraint",
            "odrl:leftOperand": {"@id": f"ab:{ref_attr}"},
            "odrl:operator": ref_operator,
            "odrl:rightOperand": {
                "@value": ref_values,
                "@type": ref_tmpl["rightOperand"]["type"],
            },
        }

        refinement_measurement_id = f"{concept}Measurement"
        constraint_block = {
            "@id": f"ab:{req_id}_Constraint",
            "@type": "odrl:Constraint",
            "odrl:leftOperand": {
                "@id": f"ab:{refinement_measurement_id}",
                "@type": constraint_tmpl["leftOperand"]["type"],
            },
            "odrl:operator": con_operator,
            "odrl:rightOperand": {
                "@value": expected_value,
                "@type": constraint_tmpl["rightOperand"]["type"],
            },
        }

        graph_nodes = [
            {
                "@id": f"ab:{req_id}Rule",
                "@type": template["policy"]["type"],
                "rdfs:label": f"ab:{req_id}Rule - QualityPolicy",
                "tb:derivedFrom": req_id,
                "tb:qualityDimension": dim,
                "tb:sourceEntity": {"@id": f"ab:{requirement['sourceEntity']}"},
                "odrl:permission": [
                    {
                        "@id": f"ab:{req_id}_Permission",
                        "@type": "odrl:Permission",
                        "odrl:action": template["policy"]["action"],
                        "odrl:assigner": {"@id": f"ab:{requirement['sourceEntity']}"},
                        "odrl:assignee": {"@id": f"ab:{template['assignee']['fixed']}"},
                        "odrl:target": {"@id": f"ab:{attribute}"},
                        "odrl:duty": [
                            {
                                "@id": f"ab:{req_id}_Duty",
                                "@type": "odrl:Duty",
                                "odrl:action": {
                                    "@id": f"ab:{req_id}_Action",
                                    "@type": "odrl:Action",
                                    "rdf:value": {"@id": f"ab:Check{dim}"},
                                    "odrl:refinement": [refinement_block],
                                },
                                "odrl:constraint": [constraint_block],
                            }
                        ],
                    }
                ],
            },
            {
                "@id": f"ab:{concept}Measurement",
                "@type": "dqv:Metric",
                "rdfs:label": f"{concept} Measurement",
                "dqv:isMeasurementOf": {"@id": f"ab:Check{concept}"},
            },
            {
                "@id": f"ab:{concept}",
                "@type": "dqv:Metric",
                "rdfs:label": f"{concept} Metric (Abstract)",
                "dqv:inDimension": {
                    "@id": f"ab:{dim}Dimension",
                    "@type": "dqv:Dimension",
                },
            },
            {
                "@id": f"ab:{dim}Dimension",
                "@type": "dqv:Dimension",
                "rdfs:label": f"{dim} ({requirement['qualityDimension']['source']})",
            },
            {
                "@id": f"ab:{attribute}",
                "@type": "odrl:Asset",
                "odrl:partOf": {"@id": ""},
            },
        ]

        return {
            "@context": template["context"],
            "@graph": graph_nodes,
        }

    # --- Standard template ---
    if "operator" in constraint_tmpl:
        odrl_operator = constraint_tmpl["operator"]
    else:
        operator_map = constraint_tmpl.get("operatorMapping", {})
        operator_symbol = (
            params.get("operator")
            or params.get("comparisonOperator")
            or params.get("comparison")
            or "="
        )
        odrl_operator = operator_map.get(operator_symbol, "odrl:eq")

    ro_tmpl = constraint_tmpl["rightOperand"]
    threshold_value = params.get(ro_tmpl["parameter"])

    if ro_tmpl["type"] == "@id":
        safe_id = str(threshold_value).replace(" ", "_").replace("\u00a0", "_")
        right_operand = {"@id": f"ab:{safe_id}"}
    else:
        right_operand = {
            "@value": str(threshold_value),
            "@type": ro_tmpl["type"],
        }

    measurement_id = f"{concept}Measurement"
    constraint_block = {
        "@id": f"ab:{req_id}_Constraint",
        "@type": "odrl:Constraint",
        "odrl:leftOperand": {
            "@id": f"ab:{measurement_id}",
            "@type": constraint_tmpl["leftOperand"]["type"],
        },
        "odrl:operator": odrl_operator,
        "odrl:rightOperand": right_operand,
    }

    if "unit" in constraint_tmpl:
        constraint_block["odrl:unit"] = {"@id": constraint_tmpl["unit"]["fixed"]}

    graph_nodes = [
        {
            "@id": f"ab:{req_id}Rule",
            "@type": template["policy"]["type"],
            "rdfs:label": f"ab:{req_id}Rule - QualityPolicy",
            "tb:derivedFrom": req_id,
            "tb:qualityDimension": dim,
            "tb:sourceEntity": {"@id": f"ab:{requirement['sourceEntity']}"},
            "odrl:permission": [
                {
                    "@id": f"ab:{req_id}_Permission",
                    "@type": "odrl:Permission",
                    "odrl:action": template["policy"]["action"],
                    "odrl:assigner": {"@id": f"ab:{requirement['sourceEntity']}"},
                    "odrl:assignee": {"@id": f"ab:{template['assignee']['fixed']}"},
                    "odrl:target": {"@id": f"ab:{attribute}"},
                    "odrl:constraint": [constraint_block],
                }
            ],
        },
        {
            "@id": f"ab:{measurement_id}",
            "@type": "dqv:Metric",
            "rdfs:label": f"{concept} Measurement",
            "dqv:isMeasurementOf": {"@id": f"ab:Check{concept}"},
        },
        {
            "@id": f"ab:{concept}",
            "@type": "dqv:Metric",
            "rdfs:label": f"{concept} Metric (Abstract)",
            "dqv:inDimension": {
                "@id": f"ab:{dim}Dimension",
                "@type": "dqv:Dimension",
            },
        },
        {
            "@id": f"ab:{dim}Dimension",
            "@type": "dqv:Dimension",
            "rdfs:label": f"{dim} ({requirement['qualityDimension']['source']})",
        },
        {
            "@id": f"ab:{attribute}",
            "@type": "odrl:Asset",
            "odrl:partOf": {"@id": ""},
        },
    ]

    if ro_tmpl["type"] == "@id" and threshold_value:
        safe_id = str(threshold_value).replace(" ", "_").replace("\u00a0", "_")
        graph_nodes.append({
            "@id": f"ab:{safe_id}",
            "@type": "tb:ReferenceStandard",
            "rdfs:label": str(threshold_value),
        })

    return {
        "@context": template["context"],
        "@graph": graph_nodes,
    }


# ========== Test Helpers ==========

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def deep_compare(generated, saved, path=""):
    """Deep compare two JSON structures, reporting differences."""
    diffs = []
    if type(generated) != type(saved):
        diffs.append(f"  {path}: type mismatch: {type(generated).__name__} vs {type(saved).__name__}")
        return diffs
    if isinstance(generated, dict):
        all_keys = set(generated.keys()) | set(saved.keys())
        for key in sorted(all_keys):
            if key not in generated:
                diffs.append(f"  {path}.{key}: MISSING in generated (saved has: {json.dumps(saved[key], ensure_ascii=False)[:80]})")
            elif key not in saved:
                diffs.append(f"  {path}.{key}: EXTRA in generated (value: {json.dumps(generated[key], ensure_ascii=False)[:80]})")
            else:
                diffs.extend(deep_compare(generated[key], saved[key], f"{path}.{key}"))
    elif isinstance(generated, list):
        if len(generated) != len(saved):
            diffs.append(f"  {path}: list length mismatch: {len(generated)} vs {len(saved)}")
        for i in range(min(len(generated), len(saved))):
            diffs.extend(deep_compare(generated[i], saved[i], f"{path}[{i}]"))
    else:
        if generated != saved:
            diffs.append(f"  {path}: value mismatch: {json.dumps(generated, ensure_ascii=False)[:60]} vs {json.dumps(saved, ensure_ascii=False)[:60]}")
    return diffs


# ========== N3 Planner Compatibility Checks ==========

def check_n3_compatibility(rule, req_id, dim):
    """Check that ODRL rule has the structure expected by N3 planner rules."""
    issues = []
    graph = rule.get("@graph", [])
    
    # Find the policy node
    policy = None
    for node in graph:
        if node.get("@id", "").endswith("Rule"):
            policy = node
            break
    
    if not policy:
        issues.append("No policy node found with @id ending in 'Rule'")
        return issues
    
    # Check required fields for N3 planner
    if policy.get("@type") != "dqv:QualityPolicy":
        issues.append(f"Policy @type should be 'dqv:QualityPolicy', got '{policy.get('@type')}'")
    
    if "tb:qualityDimension" not in policy:
        issues.append("Missing tb:qualityDimension (needed by N3 rules)")
    
    if "odrl:permission" not in policy:
        issues.append("Missing odrl:permission")
        return issues
    
    permissions = policy["odrl:permission"]
    if not isinstance(permissions, list) or len(permissions) == 0:
        issues.append("odrl:permission should be a non-empty list")
        return issues
    
    perm = permissions[0]
    
    # For Consistency (refinement-based), check duty structure
    if dim == "Consistency":
        if "odrl:duty" not in perm:
            issues.append("Consistency rule missing odrl:duty (N3 Consistency.n3 expects duty)")
            return issues
        duty = perm["odrl:duty"][0]
        action = duty.get("odrl:action", {})
        rdf_value = action.get("rdf:value", {})
        if isinstance(rdf_value, dict):
            check_id = rdf_value.get("@id", "")
        else:
            check_id = rdf_value
        if check_id != "ab:CheckConsistency":
            issues.append(f"Consistency duty action rdf:value should be ab:CheckConsistency, got '{check_id}'")
        
        refinements = action.get("odrl:refinement", [])
        if not refinements:
            issues.append("Consistency duty missing odrl:refinement on action")
        
        constraints = duty.get("odrl:constraint", [])
        if not constraints:
            issues.append("Consistency duty missing odrl:constraint")
    else:
        # Standard rules: check constraint structure
        if "odrl:constraint" not in perm:
            issues.append(f"Permission missing odrl:constraint for {dim}")
            return issues
        
        constraint = perm["odrl:constraint"][0]
        
        if "odrl:leftOperand" not in constraint:
            issues.append("Constraint missing odrl:leftOperand")
        if "odrl:operator" not in constraint:
            issues.append("Constraint missing odrl:operator")
        if "odrl:rightOperand" not in constraint:
            issues.append("Constraint missing odrl:rightOperand")
        
        # Check leftOperand has @type for N3 matching
        left = constraint.get("odrl:leftOperand", {})
        if isinstance(left, dict) and "@type" not in left:
            issues.append("Constraint leftOperand missing @type (needed for N3 matching)")
    
    # Volume-specific: check that metric has dqv:isMeasurementOf ab:CheckVolume
    measurement_concept = None
    for node in graph:
        if "dqv:isMeasurementOf" in node:
            measurement_of = node["dqv:isMeasurementOf"]
            if isinstance(measurement_of, dict):
                measurement_concept = measurement_of.get("@id")
            else:
                measurement_concept = measurement_of
    
    if dim == "Validity" and req_id == "DQR4EH":
        # DQR4EH uses Volume measurement concept
        if measurement_concept != "ab:CheckVolume":
            issues.append(f"DQR4EH: metric dqv:isMeasurementOf should be 'ab:CheckVolume', got '{measurement_concept}'")
    
    return issues


# ========== Main Test ==========

def main():
    print("=" * 80)
    print("ODRL RULE GENERATION END-TO-END TEST")
    print("=" * 80)
    
    # Mapping: requirement_id -> (pattern_id, quality_dimension)
    requirements_map = {
        "DQR1EH": ("DQRP2", "Completeness"),
        "DQR2EH": ("DQRP3", "Validity"),
        "DQR3EH": ("DQRP4", "Consistency"),
        "DQR4EH": ("DQRP5", "Validity"),  # uses measurementConcept=Volume
        "DQR5EH": ("DQRP6", "Fairness"),
        "DQR6EH": ("DQRP3", "Validity"),  # same pattern as DQR2EH
    }
    
    all_passed = True
    generated_rules = {}
    
    for req_id, (pattern_id, expected_dim) in requirements_map.items():
        print(f"\n{'─' * 60}")
        print(f"TEST: {req_id} (pattern={pattern_id}, dim={expected_dim})")
        print(f"{'─' * 60}")
        
        # Load requirement
        req_path = REQUIREMENTS_DIR / f"{req_id}.json"
        if not req_path.exists():
            print(f"  ✗ FAIL: Requirement file not found: {req_path}")
            all_passed = False
            continue
        req = load_json(req_path)
        
        # Load template
        tmpl_path = TEMPLATES_DIR / f"{pattern_id}_odrl_template.json"
        if not tmpl_path.exists():
            print(f"  ✗ FAIL: Template file not found: {tmpl_path}")
            all_passed = False
            continue
        tmpl = load_json(tmpl_path)
        
        # Verify requirement links to correct pattern
        if req["pattern"]["id"] != pattern_id:
            print(f"  ✗ FAIL: Requirement pattern mismatch: {req['pattern']['id']} != {pattern_id}")
            all_passed = False
        
        # Generate ODRL rule
        try:
            rule = build_odrl_rule(req, tmpl)
            generated_rules[req_id] = rule
            print(f"  ✓ ODRL rule generated successfully")
        except Exception as e:
            print(f"  ✗ FAIL: build_odrl_rule raised {type(e).__name__}: {e}")
            all_passed = False
            continue
        
        # Verify basic structure
        assert "@context" in rule, f"{req_id}: Missing @context"
        assert "@graph" in rule, f"{req_id}: Missing @graph"
        print(f"  ✓ Basic structure OK (@context, @graph)")
        
        # Verify policy node
        graph = rule["@graph"]
        policy_node = graph[0]
        assert policy_node["@id"] == f"ab:{req_id}Rule", f"{req_id}: Wrong policy @id"
        assert policy_node["@type"] == "dqv:QualityPolicy", f"{req_id}: Wrong @type"
        assert policy_node["tb:qualityDimension"] == expected_dim, \
            f"{req_id}: Wrong dimension: {policy_node['tb:qualityDimension']} != {expected_dim}"
        assert policy_node["tb:derivedFrom"] == req_id, f"{req_id}: Wrong derivedFrom"
        print(f"  ✓ Policy node correct (dim={expected_dim}, derivedFrom={req_id})")
        
        # Check N3 planner compatibility
        n3_issues = check_n3_compatibility(rule, req_id, expected_dim)
        if n3_issues:
            print(f"  ⚠ N3 COMPATIBILITY ISSUES:")
            for issue in n3_issues:
                print(f"    - {issue}")
        else:
            print(f"  ✓ N3 planner compatibility OK")
        
        # Compare with saved ODRL rule if exists
        saved_path = RULES_DIR / f"{req_id}_odrl.json"
        if saved_path.exists():
            saved = load_json(saved_path)
            diffs = deep_compare(rule, saved)
            if diffs:
                print(f"  ⚠ DIFFERENCES vs saved {saved_path.name}:")
                for d in diffs[:10]:
                    print(f"    {d}")
                if len(diffs) > 10:
                    print(f"    ... and {len(diffs) - 10} more")
            else:
                print(f"  ✓ Matches saved {saved_path.name} exactly")
        else:
            print(f"  ⚠ No saved ODRL rule at {saved_path} (MISSING - needs generation)")
    
    # ========== Cross-check: verify DQR7EH (Timeliness) is manually crafted ==========
    print(f"\n{'─' * 60}")
    print(f"INFO: DQR7EH (Timeliness) - manually crafted ODRL rule")
    print(f"{'─' * 60}")
    dqr7_path = RULES_DIR / "DQR7EH_odrl.json"
    if dqr7_path.exists():
        dqr7 = load_json(dqr7_path)
        n3_issues = check_n3_compatibility(dqr7, "DQR7EH", "Timeliness")
        if n3_issues:
            print(f"  ⚠ N3 COMPATIBILITY ISSUES for DQR7EH:")
            for issue in n3_issues:
                print(f"    - {issue}")
        else:
            print(f"  ✓ DQR7EH N3 compatibility OK")
        
        # Verify it has the qudt:MIN unit and dqv:computedOn expected by Timeliness.n3
        graph = dqr7.get("@graph", [])
        constraint = None
        for node in graph:
            perms = node.get("odrl:permission", [])
            for perm in perms if isinstance(perms, list) else []:
                for con in perm.get("odrl:constraint", []):
                    constraint = con
        if constraint:
            unit = constraint.get("odrl:unit", {})
            unit_id = unit.get("@id", "") if isinstance(unit, dict) else unit
            if "MIN" not in unit_id:
                print(f"  ⚠ DQR7EH constraint unit should reference qudt:MIN, got '{unit_id}'")
            else:
                print(f"  ✓ DQR7EH has qudt:MIN unit")
            
            left = constraint.get("odrl:leftOperand", {})
            if isinstance(left, dict) and "dqv:computedOn" in left:
                print(f"  ✓ DQR7EH has dqv:computedOn in leftOperand")
            else:
                print(f"  ⚠ DQR7EH missing dqv:computedOn in leftOperand (needed by Timeliness.n3)")
    else:
        print(f"  ⚠ DQR7EH_odrl.json not found")
    
    # ========== Cross-check: DQR1LS (Timeliness - LiveStocks) ==========
    print(f"\n{'─' * 60}")
    print(f"INFO: DQR1LS (Timeliness) - manually crafted ODRL rule")
    print(f"{'─' * 60}")
    dqr1ls_path = RULES_DIR / "DQR1LS_odrl.json"
    if dqr1ls_path.exists():
        dqr1ls = load_json(dqr1ls_path)
        n3_issues = check_n3_compatibility(dqr1ls, "DQR1LS", "Timeliness")
        if n3_issues:
            print(f"  ⚠ N3 COMPATIBILITY ISSUES for DQR1LS:")
            for issue in n3_issues:
                print(f"    - {issue}")
        else:
            print(f"  ✓ DQR1LS N3 compatibility OK")
        
        graph = dqr1ls.get("@graph", [])
        constraint = None
        for node in graph:
            perms = node.get("odrl:permission", [])
            for perm in perms if isinstance(perms, list) else []:
                for con in perm.get("odrl:constraint", []):
                    constraint = con
        if constraint:
            unit = constraint.get("odrl:unit", {})
            unit_id = unit.get("@id", "") if isinstance(unit, dict) else unit
            if "MIN" not in unit_id:
                print(f"  ⚠ DQR1LS constraint unit should reference qudt:MIN, got '{unit_id}'")
            else:
                print(f"  ✓ DQR1LS has qudt:MIN unit")
            
            op = constraint.get("odrl:operator")
            if op == "odrl:lteq":
                print(f"  ✓ DQR1LS operator is odrl:lteq (correct for Timeliness)")
            else:
                print(f"  ⚠ DQR1LS operator should be odrl:lteq, got '{op}'")
            
            left = constraint.get("odrl:leftOperand", {})
            if isinstance(left, dict) and "dqv:computedOn" in left:
                print(f"  ✓ DQR1LS has dqv:computedOn in leftOperand")
            else:
                print(f"  ⚠ DQR1LS missing dqv:computedOn in leftOperand (needed by Timeliness.n3)")
            
            threshold = constraint.get("odrl:rightOperand", {}).get("@value")
            if threshold == "30":
                print(f"  ✓ DQR1LS threshold is 30 minutes")
            else:
                print(f"  ⚠ DQR1LS threshold: {threshold}")
    else:
        print(f"  ⚠ DQR1LS_odrl.json not found")
    
    # ========== Operator mapping checks ==========
    print(f"\n{'─' * 60}")
    print(f"OPERATOR MAPPING CHECKS")
    print(f"{'─' * 60}")
    
    # DQR1EH: operator="at least" → should map to odrl:gteq
    dqr1_rule = generated_rules.get("DQR1EH")
    if dqr1_rule:
        constraint = dqr1_rule["@graph"][0]["odrl:permission"][0]["odrl:constraint"][0]
        op = constraint["odrl:operator"]
        print(f"  DQR1EH: operator='at least' → mapped to '{op}'")
        if op == "odrl:gteq":
            print(f"    ✓ Correct")
        else:
            print(f"    ✗ WRONG: should be 'odrl:gteq'")
            all_passed = False
    
    # DQR2EH: fixed operator odrl:isIncludedIn (no mapping, template-fixed)
    dqr2_rule = generated_rules.get("DQR2EH")
    if dqr2_rule:
        constraint = dqr2_rule["@graph"][0]["odrl:permission"][0]["odrl:constraint"][0]
        op = constraint["odrl:operator"]
        print(f"  DQR2EH: fixed operator → '{op}'")
        if op == "odrl:isIncludedIn":
            print(f"    ✓ Correct")
        else:
            print(f"    ✗ WRONG: should be 'odrl:isIncludedIn'")
            all_passed = False
    
    # DQR4EH: operator="at least" → should map to odrl:gteq
    dqr4_rule = generated_rules.get("DQR4EH")
    if dqr4_rule:
        constraint = dqr4_rule["@graph"][0]["odrl:permission"][0]["odrl:constraint"][0]
        op = constraint["odrl:operator"]
        print(f"  DQR4EH: operator='at least' → mapped to '{op}'")
        if op == "odrl:gteq":
            print(f"    ✓ Correct")
        else:
            print(f"    ✗ WRONG: should be 'odrl:gteq'")
            all_passed = False
    
    # DQR5EH: operator="not exceed" → should map to odrl:lt
    dqr5_rule = generated_rules.get("DQR5EH")
    if dqr5_rule:
        constraint = dqr5_rule["@graph"][0]["odrl:permission"][0]["odrl:constraint"][0]
        op = constraint["odrl:operator"]
        print(f"  DQR5EH: operator='not exceed' → mapped to '{op}'")
        if op == "odrl:lt":
            print(f"    ✓ Correct")
        else:
            print(f"    ✗ WRONG: should be 'odrl:lt'")
            all_passed = False
    
    # DQR6EH: fixed operator odrl:isIncludedIn (same pattern as DQR2EH)
    dqr6_rule = generated_rules.get("DQR6EH")
    if dqr6_rule:
        constraint = dqr6_rule["@graph"][0]["odrl:permission"][0]["odrl:constraint"][0]
        op = constraint["odrl:operator"]
        print(f"  DQR6EH: fixed operator → '{op}'")
        if op == "odrl:isIncludedIn":
            print(f"    ✓ Correct")
        else:
            print(f"    ✗ WRONG: should be 'odrl:isIncludedIn'")
            all_passed = False
    
    # ========== PolicyChecker Steps Validation ==========
    print(f"\n{'─' * 60}")
    print(f"POLICY CHECKER STEPS VALIDATION")
    print(f"{'─' * 60}")
    
    # For each rule, validate that the ODRL structure contains all fields
    # that each N3 rule needs to fire a complete operation chain.
    # Each N3 rule creates: LoadData → CheckX → Constraint (terminal)
    
    step_checks = {
        "DQR1EH": {
            "n3_rule": "Completeness.n3",
            "chain": "LoadData → CheckCompleteness → Constraint",
            "checks": [
                ("tb:qualityDimension == 'Completeness'", lambda r: r["@graph"][0].get("tb:qualityDimension") == "Completeness"),
                ("permission has odrl:constraint", lambda r: "odrl:constraint" in r["@graph"][0]["odrl:permission"][0]),
                ("constraint has leftOperand with @type", lambda r: "@type" in r["@graph"][0]["odrl:permission"][0]["odrl:constraint"][0]["odrl:leftOperand"]),
                ("constraint has odrl:operator", lambda r: "odrl:operator" in r["@graph"][0]["odrl:permission"][0]["odrl:constraint"][0]),
                ("constraint has odrl:rightOperand", lambda r: "odrl:rightOperand" in r["@graph"][0]["odrl:permission"][0]["odrl:constraint"][0]),
                ("constraint has odrl:unit (qudt:PERCENT)", lambda r: r["@graph"][0]["odrl:permission"][0]["odrl:constraint"][0].get("odrl:unit", {}).get("@id") == "qudt:PERCENT"),
                ("metric isMeasurementOf ab:CheckCompleteness", lambda r: any(n.get("dqv:isMeasurementOf", {}).get("@id") == "ab:CheckCompleteness" for n in r["@graph"] if "dqv:isMeasurementOf" in n)),
                ("permission has odrl:target", lambda r: "odrl:target" in r["@graph"][0]["odrl:permission"][0]),
            ],
        },
        "DQR2EH": {
            "n3_rule": "Validity.n3",
            "chain": "LoadData → CheckValidity → Constraint",
            "checks": [
                ("tb:qualityDimension == 'Validity'", lambda r: r["@graph"][0].get("tb:qualityDimension") == "Validity"),
                ("permission has odrl:constraint", lambda r: "odrl:constraint" in r["@graph"][0]["odrl:permission"][0]),
                ("constraint operator is odrl:isIncludedIn", lambda r: r["@graph"][0]["odrl:permission"][0]["odrl:constraint"][0]["odrl:operator"] == "odrl:isIncludedIn"),
                ("rightOperand is @id reference (ab:ISO_3166)", lambda r: r["@graph"][0]["odrl:permission"][0]["odrl:constraint"][0]["odrl:rightOperand"].get("@id") == "ab:ISO_3166"),
                ("metric isMeasurementOf ab:CheckValidity", lambda r: any(n.get("dqv:isMeasurementOf", {}).get("@id") == "ab:CheckValidity" for n in r["@graph"] if "dqv:isMeasurementOf" in n)),
                ("ReferenceStandard node exists", lambda r: any(n.get("@type") == "tb:ReferenceStandard" for n in r["@graph"])),
            ],
        },
        "DQR3EH": {
            "n3_rule": "Consistency.n3",
            "chain": "LoadData → CheckConsistency (terminal)",
            "checks": [
                ("tb:qualityDimension == 'Consistency'", lambda r: r["@graph"][0].get("tb:qualityDimension") == "Consistency"),
                ("permission has odrl:duty", lambda r: "odrl:duty" in r["@graph"][0]["odrl:permission"][0]),
                ("duty action has rdf:value ab:CheckConsistency", lambda r: r["@graph"][0]["odrl:permission"][0]["odrl:duty"][0]["odrl:action"]["rdf:value"]["@id"] == "ab:CheckConsistency"),
                ("action has odrl:refinement", lambda r: "odrl:refinement" in r["@graph"][0]["odrl:permission"][0]["odrl:duty"][0]["odrl:action"]),
                ("refinement leftOperand is ab:gender", lambda r: r["@graph"][0]["odrl:permission"][0]["odrl:duty"][0]["odrl:action"]["odrl:refinement"][0]["odrl:leftOperand"]["@id"] == "ab:gender"),
                ("refinement rightOperand is 'male'", lambda r: r["@graph"][0]["odrl:permission"][0]["odrl:duty"][0]["odrl:action"]["odrl:refinement"][0]["odrl:rightOperand"]["@value"] == "male"),
                ("duty has odrl:constraint", lambda r: "odrl:constraint" in r["@graph"][0]["odrl:permission"][0]["odrl:duty"][0]),
                ("duty constraint rightOperand is 'NULL'", lambda r: r["@graph"][0]["odrl:permission"][0]["odrl:duty"][0]["odrl:constraint"][0]["odrl:rightOperand"]["@value"] == "NULL"),
                ("permission target is ab:pregnancyHistory", lambda r: r["@graph"][0]["odrl:permission"][0]["odrl:target"]["@id"] == "ab:pregnancyHistory"),
            ],
        },
        "DQR4EH": {
            "n3_rule": "Volume.n3",
            "chain": "LoadData → CheckVolume → Constraint",
            "checks": [
                ("tb:qualityDimension == 'Validity'", lambda r: r["@graph"][0].get("tb:qualityDimension") == "Validity"),
                ("permission has odrl:constraint", lambda r: "odrl:constraint" in r["@graph"][0]["odrl:permission"][0]),
                ("constraint operator is odrl:gteq", lambda r: r["@graph"][0]["odrl:permission"][0]["odrl:constraint"][0]["odrl:operator"] == "odrl:gteq"),
                ("constraint rightOperand value is '2000'", lambda r: r["@graph"][0]["odrl:permission"][0]["odrl:constraint"][0]["odrl:rightOperand"]["@value"] == "2000"),
                ("constraint unit is qudt:NUMBER", lambda r: r["@graph"][0]["odrl:permission"][0]["odrl:constraint"][0].get("odrl:unit", {}).get("@id") == "qudt:NUMBER"),
                ("metric isMeasurementOf ab:CheckVolume", lambda r: any(n.get("dqv:isMeasurementOf", {}).get("@id") == "ab:CheckVolume" for n in r["@graph"] if "dqv:isMeasurementOf" in n)),
                ("VolumeMeasurement node exists", lambda r: any(n.get("@id") == "ab:VolumeMeasurement" for n in r["@graph"])),
            ],
        },
        "DQR5EH": {
            "n3_rule": "Fairness.n3",
            "chain": "LoadData → CheckFairness → Constraint",
            "checks": [
                ("tb:qualityDimension == 'Fairness'", lambda r: r["@graph"][0].get("tb:qualityDimension") == "Fairness"),
                ("permission has odrl:constraint", lambda r: "odrl:constraint" in r["@graph"][0]["odrl:permission"][0]),
                ("constraint operator is odrl:lt", lambda r: r["@graph"][0]["odrl:permission"][0]["odrl:constraint"][0]["odrl:operator"] == "odrl:lt"),
                ("constraint rightOperand value is '5'", lambda r: r["@graph"][0]["odrl:permission"][0]["odrl:constraint"][0]["odrl:rightOperand"]["@value"] == "5"),
                ("constraint unit is qudt:PERCENT", lambda r: r["@graph"][0]["odrl:permission"][0]["odrl:constraint"][0].get("odrl:unit", {}).get("@id") == "qudt:PERCENT"),
                ("metric isMeasurementOf ab:CheckFairness", lambda r: any(n.get("dqv:isMeasurementOf", {}).get("@id") == "ab:CheckFairness" for n in r["@graph"] if "dqv:isMeasurementOf" in n)),
                ("permission target is ab:gender", lambda r: r["@graph"][0]["odrl:permission"][0]["odrl:target"]["@id"] == "ab:gender"),
            ],
        },
        "DQR6EH": {
            "n3_rule": "Validity.n3",
            "chain": "LoadData → CheckValidity → Constraint",
            "checks": [
                ("tb:qualityDimension == 'Validity'", lambda r: r["@graph"][0].get("tb:qualityDimension") == "Validity"),
                ("constraint operator is odrl:isIncludedIn", lambda r: r["@graph"][0]["odrl:permission"][0]["odrl:constraint"][0]["odrl:operator"] == "odrl:isIncludedIn"),
                ("rightOperand is @id reference (ab:ISO_3166_International_Standard)", lambda r: r["@graph"][0]["odrl:permission"][0]["odrl:constraint"][0]["odrl:rightOperand"].get("@id") == "ab:ISO_3166_International_Standard"),
                ("ReferenceStandard label is 'ISO 3166 International Standard'", lambda r: any(n.get("rdfs:label") == "ISO 3166 International Standard" for n in r["@graph"] if n.get("@type") == "tb:ReferenceStandard")),
                ("permission target is ab:country", lambda r: r["@graph"][0]["odrl:permission"][0]["odrl:target"]["@id"] == "ab:country"),
            ],
        },
    }
    
    for req_id, spec in step_checks.items():
        rule = generated_rules.get(req_id)
        if not rule:
            print(f"  ✗ {req_id}: rule not generated (skipping)")
            all_passed = False
            continue
        
        print(f"  {req_id} → {spec['n3_rule']} [{spec['chain']}]")
        for check_name, check_fn in spec["checks"]:
            try:
                result = check_fn(rule)
                if result:
                    print(f"    ✓ {check_name}")
                else:
                    print(f"    ✗ FAIL: {check_name}")
                    all_passed = False
            except Exception as e:
                print(f"    ✗ ERROR: {check_name} → {type(e).__name__}: {e}")
                all_passed = False
    
    # ========== PolicyChecker Coverage ==========
    print(f"\n{'─' * 60}")
    print(f"POLICY CHECKER COVERAGE")
    print(f"{'─' * 60}")
    
    # Expected rules and their matching N3 rules
    coverage = {
        "DQR1EH": ("Completeness.n3", "Matches on tb:qualityDimension='Completeness', odrl:constraint"),
        "DQR2EH": ("Validity.n3", "Matches on tb:qualityDimension='Validity', odrl:constraint"),
        "DQR3EH": ("Consistency.n3", "Matches on tb:qualityDimension='Consistency', odrl:duty with refinement"),
        "DQR4EH": ("Volume.n3", "Matches on dqv:isMeasurementOf=ab:CheckVolume (cross-dimension)"),
        "DQR5EH": ("Fairness.n3", "Matches on tb:qualityDimension='Fairness', odrl:constraint"),
        "DQR6EH": ("Validity.n3", "Matches on tb:qualityDimension='Validity', odrl:constraint"),
        "DQR7EH": ("Timeliness.n3", "Matches on tb:qualityDimension='Timeliness', odrl:unit=qudt:MIN"),
        "DQR1LS": ("Timeliness.n3", "Matches on tb:qualityDimension='Timeliness', odrl:unit=qudt:MIN"),
    }
    
    n3_dir = Path("Connector/ValidationFramework/planner/rules_n3")
    for rule_id, (n3_file, desc) in coverage.items():
        has_odrl = (RULES_DIR / f"{rule_id}_odrl.json").exists()
        has_n3 = (n3_dir / n3_file).exists()
        status = "✓" if (has_odrl and has_n3) else "✗ MISSING"
        if not has_odrl:
            status += " (no ODRL rule)"
        if not has_n3:
            status += " (no N3 rule)"
        print(f"  {status} {rule_id} → {n3_file}: {desc}")
    
    # ========== Summary ==========
    print(f"\n{'=' * 80}")
    if all_passed:
        print("ALL TESTS PASSED ✓")
    else:
        print("SOME TESTS FAILED ✗")
    print(f"{'=' * 80}")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
