"""
N3 Logic-Based Policy Planner for Federated Data Validation Framework
========================================================================

This module implements the PLANNER phase using N3 logic rules with automatic rule chaining.
It generates Policy Checkers (validation plans) from ODRL policies and data contracts
by applying declarative N3 reasoning rules to the Semantic Data Model (SDM).

Key Features:
    - Uses N3 logic rules (declarative) instead of SPARQL CONSTRUCT (procedural)
    - Automatic rule chaining via pattern matching (no procedural layers)
    - Leverages EYE reasoner for rule application
    - Custom skolemization for clean URI generation (abox:genid-<hash>)
    - Unified rule directory for all policy transformations

Architecture:
    1. N3DCParser reads data contracts and policies from SDM
    2. All N3 rules are applied in single pass via EYE reasoner
    3. Rules chain automatically based on pattern matching
    4. PolicyChecker graphs define executable validation workflows
    5. Results with clean URIs are appended to SDM

Author: acraf
Version: 3.0.0-unified
Last Updated: December 11, 2025
"""

import subprocess
import tempfile
import hashlib
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict
import logging

from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS, BNode

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# NAMESPACE DEFINITIONS
# ============================================================================

# Core namespaces
tbox = Namespace("http://www.semanticweb.org/acraf/ontologies/2024/healthmesh/tbox#")
abox = Namespace("http://www.semanticweb.org/acraf/ontologies/2024/healthmesh/abox#")
tb = tbox  # Alias for compatibility

# Standard namespaces
odrl = Namespace("http://www.w3.org/ns/odrl/2/")
dqv = Namespace("http://www.w3.org/ns/dqv#")
dcat = Namespace("http://www.w3.org/ns/dcat#")

# N3 reasoning namespaces
log = Namespace("http://www.w3.org/2000/10/swap/log#")
math = Namespace("http://www.w3.org/2000/10/swap/math#")
string = Namespace("http://www.w3.org/2000/10/swap/string#")


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class N3PlannerConfig:
    """Configuration for N3-based planner with unified rule chaining"""
    n3_reasoner: str = "eye"  # or "cwm"
    enable_proof_generation: bool = False
    reasoner_timeout: int = 30
    rules_directory: str = "rules_n3_unified"  # Unified rule chaining directory
    eye_path: str = "eye"  # Path to EYE reasoner executable
    timeout: int = 30  # Reasoner timeout in seconds
    n3_query_all: str = """
@prefix : <http://www.w3.org/2000/10/swap/log#> .
{ ?s ?p ?o } => { ?s ?p ?o } .
"""  # N3 query to extract all inferred triples


# ============================================================================
# N3 POLICY CHECKER
# ============================================================================

class N3PolicyChecker:
    """Represents a PolicyChecker using N3 reasoning"""
    
    def __init__(self, policy_uri: URIRef, dp_uri: URIRef):
        self.policy = policy_uri
        self.dp = dp_uri
        self.graph = Graph()
        
        # Bind namespaces
        self.graph.bind("tb", tb)
        self.graph.bind("tbox", tbox)
        self.graph.bind("abox", abox)
        self.graph.bind("odrl", odrl)
        
    def get_graph(self):
        return self.graph


# ============================================================================
# N3 DATA CONTRACT PARSER
# ============================================================================

class N3DCParser:
    """
    Parse Data Contract Policies using N3 logic rules with automatic chaining
    
    This replaces the SPARQL-based DCParser with declarative N3 reasoning.
    Rules automatically chain based on pattern matching - no procedural layers needed.
    """
    
    def __init__(self, dp: str, graph: Graph, config: Optional[N3PlannerConfig] = None):
        """
        Initialize N3DCParser
        
        Args:
            dp: Data product name
            graph: RDF graph containing SDM
            config: Configuration object (uses defaults if not provided)
        """
        self.dp = dp
        self.g = graph
        self.config = config or N3PlannerConfig()
        self.attr_mappings = {}
        
        # Bind namespaces
        self.g.bind("tb", tb)
        self.g.bind("tbox", tbox)
        self.g.bind("abox", abox)
        self.g.bind("odrl", odrl)
        self.g.bind("dqv", dqv)
        self.g.bind("log", log)
        self.g.bind("math", math)
        self.g.bind("string", string)
        
    def _read_contracts(self) -> Tuple[List[URIRef], Dict[str, str]]:
        """
        Get the policies and mappings associated with a data product
        
        Returns:
            Tuple of (policies_list, mappings_dict)
        """
        dp_uri = abox[self.dp]
        contracts = self.g.objects(subject=dp_uri, predicate=tb.hasDC)
        policies_list = []
        mappings_dict = {}
        
        for contract in contracts:
            # Handle policies
            policies = self.g.objects(subject=contract, predicate=tb.hasPolicy)
            for policy in policies:
                policies_list.append(policy)
                
            # Handle mappings
            mappings = self.g.objects(subject=contract, predicate=tb.hasMapping)
            for mapping in mappings:
                mfrom = self.g.value(subject=mapping, predicate=tb.mfrom)
                mto = self.g.value(subject=mapping, predicate=tb.mto)
                if mfrom and mto:
                    mappings_dict[str(mto)] = str(mfrom)
                    
        self.attr_mappings = mappings_dict
        return policies_list, mappings_dict
    
    def _execute_n3_rules(self, subdirectory: str = "") -> Graph:
        """
        Execute N3 rules from the configured rules directory
        
        All rules are executed together, allowing automatic chaining via pattern matching.
        Custom skolemization creates clean URIs (abox:genid-<hash>) instead of verbose defaults.
        
        Args:
            subdirectory: Optional subdirectory within rules_directory (empty for unified rules)
            
        Returns:
            Graph containing inferred triples with skolemized URIs
        """
        rules_path = Path(self.config.rules_directory)
        if subdirectory:
            rules_path = rules_path / subdirectory
        
        if not rules_path.exists():
            logger.warning(f"Rules directory not found: {rules_path}")
            return Graph()
        
        # Prepare data as temporary N3 file
        # Create a new graph and copy triples (Graph doesn't have .copy() method)
        data_graph = Graph()
        for s, p, o in self.g:
            data_graph.add((s, p, o))
        
        # Bind namespaces to data graph
        data_graph.bind("tb", tb)
        data_graph.bind("tbox", tbox)
        data_graph.bind("abox", abox)
        data_graph.bind("odrl", odrl)
        data_graph.bind("dqv", dqv)
        
        # Collect all .n3 rule files
        rule_files = list(rules_path.glob("*.n3"))
        
        if not rule_files:
            logger.warning(f"No .n3 files found in {rules_path}")
            return Graph()
        
        # Write data to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.n3', delete=False) as f:
            data_file = f.name
            f.write(data_graph.serialize(format='n3'))
        
        # Write query file (construct all triples)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.n3', delete=False) as qf:
            query_file = qf.name
            qf.write(self.config.n3_query_all)
        
        try:
            # Build EYE command with all rule files
            cmd = [
                self.config.eye_path,
                data_file,
                *[str(rf) for rf in rule_files],
                "--query", query_file,
                "--nope"
            ]
            
            logger.debug(f"Running EYE with {len(rule_files)} rules")
            
            # Run EYE reasoner
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout
            )
            
            if result.returncode != 0:
                logger.error(f"EYE reasoner error: {result.stderr}")
                return Graph()
            
            # Parse output N3
            output_g = Graph()
            output_g.parse(data=result.stdout, format='n3')
            
            # Apply custom skolemization to replace RDFLib's blank nodes with clean URIs
            skolem_g = Graph()
            bnode_map = {}
            
            for s, p, o in output_g:
                # Skolemize subject
                if isinstance(s, BNode):
                    if s not in bnode_map:
                        # Create clean hash-based URI using abox namespace
                        hash_val = hashlib.md5(str(s).encode()).hexdigest()[:12]
                        bnode_map[s] = abox[f"genid-{hash_val}"]
                    s = bnode_map[s]
                
                # Skolemize object
                if isinstance(o, BNode):
                    if o not in bnode_map:
                        hash_val = hashlib.md5(str(o).encode()).hexdigest()[:12]
                        bnode_map[o] = abox[f"genid-{hash_val}"]
                    o = bnode_map[o]
                
                skolem_g.add((s, p, o))
            
            logger.info(f"Inferred {len(skolem_g)} triples from {len(rule_files)} rules")
            return skolem_g
            
        except subprocess.TimeoutExpired:
            logger.error(f"EYE reasoner timeout after {self.config.timeout}s")
            return Graph()
        except Exception as e:
            logger.error(f"Error running EYE reasoner: {e}")
            return Graph()
        finally:
            # Clean up temp files
            Path(data_file).unlink(missing_ok=True)
            Path(query_file).unlink(missing_ok=True)
    
    def _apply_attribute_mappings(self):
        """
        Apply attribute mappings to operations that reference CDM attributes
        
        Replaces Common Data Model (CDM) attribute references with actual
        data product attribute names based on mappings in the data contract.
        """
        for cdm_attr, actual_attr in self.attr_mappings.items():
            # Find all triples with CDM attribute as object
            triples_to_update = []
            for s, p, o in self.g:
                if str(o) == cdm_attr:
                    triples_to_update.append((s, p, o))
            
            # Update triples
            for s, p, o in triples_to_update:
                self.g.remove((s, p, o))
                self.g.add((s, p, URIRef(actual_attr)))
    
    def parse_contracts(self) -> Graph:
        """
        Main parsing method - executes all N3 rules in a single pass.
        Rule chaining happens automatically via pattern matching.
        
        Process:
            1. Read policies and attribute mappings from data contracts
            2. Execute all N3 rules together (chaining happens automatically)
            3. Apply attribute mappings to generated operations
            4. Return enhanced graph with PolicyCheckers and Operations
        
        Returns:
            Graph containing PolicyCheckers and Operation chains
        """
        logger.info(f"Parsing contracts for data product: {self.dp}")
        
        # Step 1: Read contracts
        policies, mappings = self._read_contracts()
        logger.info(f"Found {len(policies)} policies and {len(mappings)} attribute mappings")
        
        # Step 2: Execute all unified rules (chaining happens automatically)
        logger.info("Executing N3 rules with automatic chaining...")
        result = self._execute_n3_rules("")  # Empty string = no subdirectory
        
        if len(result) > 0:
            self.g += result
            
            # Count PolicyCheckers created
            pcs = list(self.g.subjects(RDF.type, tbox.PolicyChecker))
            ops = list(self.g.subjects(RDF.type, tbox.Operation))
            
            logger.info(f"Created {len(pcs)} PolicyChecker(s) and {len(ops)} operations")
        else:
            logger.warning("Rules produced no results")
        
        # Step 3: Apply attribute mappings
        if self.attr_mappings:
            logger.info("Applying attribute mappings to operations...")
            self._apply_attribute_mappings()
        
        logger.info(f"Parsing complete. Total triples: {len(self.g)}")
        return self.g
    
    def validate_policy_checkers(self, shacl_shape_file: str = None) -> Tuple[bool, Graph, str]:
        """
        Validate PolicyCheckers using SHACL shapes
        
        Args:
            shacl_shape_file: Path to SHACL shape file (defaults to policy_checker_shape.ttl)
            
        Returns:
            Tuple of (conforms: bool, report_graph: Graph, report_text: str)
        """
        try:
            from pyshacl import validate
        except ImportError:
            logger.warning("pyshacl not installed - skipping validation")
            return True, Graph(), "pyshacl not available"
        
        # Default shape file
        if shacl_shape_file is None:
            shacl_shape_file = str(Path(__file__).parent / "policy_checker_shape.ttl")
        
        if not Path(shacl_shape_file).exists():
            logger.warning(f"SHACL shape file not found: {shacl_shape_file}")
            return True, Graph(), "Shape file not found"
        
        # Load SHACL shapes
        shapes_graph = Graph()
        shapes_graph.parse(shacl_shape_file, format='turtle')
        
        logger.info("Validating PolicyCheckers with SHACL...")
        
        # Validate
        conforms, report_graph, report_text = validate(
            self.g,
            shacl_graph=shapes_graph,
            inference='rdfs',
            abort_on_first=False,
            meta_shacl=False,
            debug=False
        )
        
        if conforms:
            logger.info("✓ PolicyChecker validation passed")
        else:
            logger.error("✗ PolicyChecker validation failed")
            logger.error(report_text)
        
        return conforms, report_graph, report_text


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Example usage of N3DCParser"""
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python planner_n3.py <sdm_file> <data_product_name>")
        sys.exit(1)
    
    sdm_file = sys.argv[1]
    dp_name = sys.argv[2]
    
    # Load SDM
    logger.info(f"Loading SDM from {sdm_file}")
    sdm = Graph()
    sdm.parse(sdm_file, format='turtle')
    
    # Create parser and parse contracts
    config = N3PlannerConfig()
    parser = N3DCParser(dp_name, sdm, config)
    result = parser.parse_contracts()
    
    # Validate PolicyCheckers
    conforms, report_graph, report_text = parser.validate_policy_checkers()
    if not conforms:
        logger.error("Validation failed - check errors above")
        sys.exit(1)
    
    # Save result
    output_file = sdm_file.replace('.ttl', '_with_pcs.ttl')
    result.serialize(destination=output_file, format='turtle')
    logger.info(f"Saved enhanced SDM to {output_file}")


if __name__ == "__main__":
    main()
