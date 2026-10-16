# Scripts

Small utilities that used to sit at the repository root. Run them from the root, since their paths are relative to it.

| Script | What it does |
| ------ | ------------ |
| `extract_udfs.py` | Lists, from the semantic data model (`FederatedComputationalGovernance/SemanticDataModel/sdm.ttl`), the code generated for each policy checker. |
| `test_odrl_generation.py` | Checks that the catalogue prototype builds the expected ODRL rule for each EHDS DQR. The maintained version is `FederatedComputationalGovernance/ComputationalCatalogues/prototype/test_odrl_generation.py`. |
| `query.n3` | Identity rule (`{ ?s ?p ?o } => { ?s ?p ?o }`) for printing a graph with the EYE reasoner. |

Example: `python scripts/extract_udfs.py`
