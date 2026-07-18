import json
import logging
from rdflib import Namespace, RDF, URIRef
from app import build_ontology, validate_graph, graph_to_json, load_bao_labels
import tomllib as toml

def run():
    print("Mocking extraction result...")
    result = {
        "document_metadata": {},
        "entities": [
            {"text": "GLP-1 receptor agonist", "category": "Compound", "normalized_name": "GLP1ReceptorAgonist"},
            {"text": "SEQ ID NO 15", "category": "Compound", "normalized_name": "SEQIDNO15"},
            {"text": "binding assay", "category": "Assay", "normalized_name": "BindingAssay"},
            {"text": "IC50", "category": "Measurement", "normalized_name": "IC50"},
            {"text": "DPP-IV", "category": "Target", "normalized_name": "DPPIV", "identifier": "NCBIGENE:1040"},
            {"text": "Native glucagon", "category": "Compound", "normalized_name": "NativeGlucagon", "identifier": "CHEBI:5391"}
        ],
        "relationships": [
            {"source": "GLP1ReceptorAgonist", "predicate": "hasMember", "target": "SEQIDNO15"}
        ]
    }
    
    print("Building ontology...")
    bao_labels = load_bao_labels()
    g = build_ontology(result, "AU2022231763B2-2.pdf", "12345", "test_text", bao_labels)
    
    # Inject a dummy BAO edge between an Assay and a Measurement to simulate the regression test
    NS = Namespace("http://ai-ontology.com/assay-ontology/")
    BAO = Namespace("http://www.bioassayontology.org/bao#")
    
    assay_node = NS["Assay_BindingAssay"]
    meas_node = NS["Measurement_IC50"]
    g.add((assay_node, BAO.BAO_0000208, meas_node))
    
    print("\n--- JSON EXPORT REGRESSION TEST ---")
    json_export = graph_to_json(g)
    
    unknowns = [n for n in json_export["nodes"] if n["type"] == "Unknown"]
    if unknowns:
        print(f"FAILED: Found {len(unknowns)} nodes with type='Unknown'!")
    else:
        print("PASSED: 0 nodes with type='Unknown'.")
        
    # Test for BAO edge
    edges = json_export["edges"]
    bao_edges = [e for e in edges if e["relation"] == "BAO_0000208"]
    if bao_edges:
        print(f"PASSED: Found {len(bao_edges)} BAO edges in JSON export!")
    else:
        print("FAILED: Did NOT find BAO edges in JSON export!")
        
    # Check NCBI links
    print("\n--- NCBI LINK CHECK ---")
    bad_links = False
    for s, p, o in g.triples((None, NS.ncbiLink, None)):
        if "uniprot" in str(o) or "ebi.ac.uk" in str(o):
            bad_links = True
            print(f"FAILED: Found non-NCBI link in xref property: {o}")
            
    if not bad_links:
        print("PASSED: No UniProt/ChEBI/EBI links found in DP_DB_XREF!")
        
    # Check hasMember logic
    has_member_edges = [e for e in edges if e["relation"] == "hasMember"]
    print(f"Found {len(has_member_edges)} hasMember edges in the extracted graph:")
    for e in has_member_edges:
        print(f"  {e['source']} -> hasMember -> {e['target']}")
        
    for n in json_export["nodes"]:
        if "SEQIDNO15" in n["id"] and "GLP1" in n["id"]:
            print(f"FAILED: Found malformed merged node: {n['id']}")

    print("\nDone.")

if __name__ == "__main__":
    run()
