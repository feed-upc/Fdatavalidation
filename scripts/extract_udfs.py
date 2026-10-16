from rdflib import Graph, Namespace
import sys

sdm_path = "FederatedComputationalGovernance/SemanticDataModel/sdm.ttl"
g = Graph()
g.parse(sdm_path, format="turtle")

tb = Namespace("http://www.semanticweb.org/acraf/ontologies/2024/healthmesh/tbox#")

q = """
PREFIX tb: <http://www.semanticweb.org/acraf/ontologies/2024/healthmesh/tbox#>
PREFIX prov: <http://www.w3.org/ns/prov#>

SELECT ?policy ?dataset ?code WHERE {
    ?pc a tb:PolicyChecker ;
        tb:accordingTo ?policy ;
        tb:validates ?dataset ;
        tb:hasValidationReport ?report .
    ?report tb:hasComposedCode ?code .
}
"""

for row in g.query(q):
    policy = str(row.policy).split('#')[-1]
    dataset = str(row.dataset).split('#')[-1]
    print(f"=== UDF for {policy} on {dataset} ===")
    print(str(row.code))
    print()
