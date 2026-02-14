from rdflib import Graph, Namespace, RDF
import sys

# Namespaces
tb = Namespace("http://www.semanticweb.org/acraf/ontologies/2024/healthmesh/tbox#")
prov = Namespace("http://www.w3.org/ns/prov#")

def generate_udf_content():
    g = Graph()
    try:
        g.parse('FederatedComputationalGovernance/SemanticDataModel/sdm.ttl', format='turtle')
    except Exception as e:
        return f"Error loading SDM: {e}"

    output = []
    
    # Iterate over all reports with composed code
    reports = list(g.subject_objects(tb.hasComposedCode))
    
    if not reports:
        return "❌ No composed code found in SDM."
        
    for report_uri, composed_code in reports:
        # Identify the PolicyChecker
        pc_uri = g.value(report_uri, prov.wasGeneratedBy)
        if not pc_uri:
            for pc in g.subjects(tb.hasValidationReport, report_uri):
                pc_uri = pc
                break
        
        policy_name = "Unknown Policy"
        if pc_uri:
            policy_uri = g.value(pc_uri, tb.accordingTo)
            if policy_uri:
                policy_name = policy_uri.split('#')[-1]

        # Identify dependencies via Implementations
        dependencies = set()
        if pc_uri:
            current = g.value(pc_uri, tb.nextStep)
            seen = set()
            while current and current not in seen:
                seen.add(current)
                impl = g.value(current, tb.hasImplementation)
                if impl:
                    for dep in g.objects(impl, tb.dependsOn):
                        dep_name = g.value(dep, tb.name)
                        if dep_name:
                            dependencies.add(str(dep_name))
                current = g.value(current, tb.nextStep)

        # Construct content for this report
        content = []
        content.append('"""')
        content.append(f'Standalone UDF generated from Report: {report_uri.split("#")[-1]}')
        content.append(f'Policy: {policy_name}')
        content.append('"""')
        content.append("")
        
        content.append("# Imports derived from tb:dependsOn")
        if "pandas" in dependencies:
            content.append("import pandas as pd")
            content.append("import pandas")
        if "datetime" in dependencies:
            content.append("from datetime import datetime")
        if "pydicom" in dependencies:
            content.append("import pydicom")
            
        content.append("")
        content.append(f"# Composed Pipeline Code for {policy_name}")
        content.append(str(composed_code))
        content.append("")
        content.append("-" * 40)
        content.append("")
        
        output.append("\n".join(content))
    
    return "\n".join(output)

if __name__ == "__main__":
    print(generate_udf_content())
