import json
from app import build_ontology, graph_to_json, load_bao_labels
from rdflib import Namespace, RDF

def run():
    print("Mocking extraction result...")
    result = {
        "document_metadata": {},
        "entities": [
            {"text": "Semaglutide", "category": "Compound", "normalized_name": "Semaglutide", "modality": "Peptide", "developmentStage": "Phase 2"},
            {"text": "Lilly Research Laboratories", "category": "Organization", "normalized_name": "LillyResearchLaboratories"},
            {"text": "Eli Lilly and Company", "category": "Organization", "normalized_name": "EliLilly"},
            {"text": "compound X", "category": "Compound", "normalized_name": "CompoundX", "modality": "Small Molecule"}
        ],
        "relationships": [
            {"source": "EliLilly", "predicate": "hasSubsidiary", "target": "LillyResearchLaboratories"},
            {"source": "CompoundX", "predicate": "developedBy", "target": "LillyResearchLaboratories"}
        ]
    }
    
    bao_labels = load_bao_labels()
    g = build_ontology(result, "TEST.pdf", "000", "Lilly Research Laboratories, a division of Eli Lilly and Company, developed compound X", bao_labels)
    
    print("\n--- JSON EXPORT REGRESSION TEST ---")
    json_export = graph_to_json(g)
    
    unknowns = [n for n in json_export["nodes"] if n["type"] == "Unknown"]
    if unknowns:
        print(f"FAILED: Found {len(unknowns)} nodes with type='Unknown'!")
        for n in unknowns:
            print(f" - {n['id']}")
    else:
        print("PASSED: 0 nodes with type='Unknown'.")
        
    orgs = [n for n in json_export["nodes"] if n["type"] == "Organization"]
    print(f"Found {len(orgs)} organizations in JSON: {[o['id'] for o in orgs]}")
    
    edges = json_export["edges"]
    developedBy = [e for e in edges if e.get("title") == "developedBy"]
    hasSubsidiary = [e for e in edges if e.get("title") == "hasSubsidiary"]
    
    print(f"Found {len(developedBy)} developedBy edges.")
    print(f"Found {len(hasSubsidiary)} hasSubsidiary edges.")

if __name__ == "__main__":
    run()
