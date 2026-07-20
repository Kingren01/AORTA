"""
Assay-Centric Ontology Pipeline  –  V2
Ontology-driven competitive intelligence for early R&D.

Run: streamlit run app.py

Backend configuration (.streamlit/secrets.toml):
  DATABRICKS_HOST  = "https://dbc-xxxxxxxx.cloud.databricks.com"
  DATABRICKS_TOKEN = "dapi..."
  DATABRICKS_MODEL = "system.ai.gpt-5-5-pro"
  NCBI_API_KEY     = "..."          # optional
"""

from __future__ import annotations

import io
import time
import json
import uuid
import os
import re
import tempfile
import textwrap
import mimetypes
from pathlib import Path
from typing import Any

# Register custom MIME types to fix Streamlit UUID download bug for unknown extensions
mimetypes.add_type("application/rdf+xml", ".owl")
mimetypes.add_type("text/turtle", ".ttl")

import pandas as pd
import requests
import streamlit as st
from pyvis.network import Network
from rdflib import BNode, Graph, Literal, Namespace, RDF, RDFS, URIRef
from rdflib.namespace import OWL, XSD

from chatbot_tools import TOOL_SCHEMAS
from chatbot_llm import (
    run_chatbot_loop_stream, run_chatbot_loop,
    STEP_SENDING, STEP_TOOL_REQ, STEP_TOOL_EXEC,
    STEP_TOOL_DONE, STEP_FEEDING, STEP_DONE, STEP_ERROR,
)
import chat_storage
from vector_db import vector_db

# Optional imports for document parsing (gracefully degrade)
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None


# ---------------------------------------------------------------------------
# Constants & Namespace setup
# ---------------------------------------------------------------------------

ONTOLOGY_IRI = "http://ai-ontology.com/assay-ontology"
BASE_URI = ONTOLOGY_IRI + "/"
NS = Namespace(BASE_URI)
BAO = Namespace("http://www.bioassayontology.org/bao#")
OBO = Namespace("http://purl.obolibrary.org/obo/")

CLASS_URIS = {
    "Target": NS.Target,
    "Pathway": NS.Pathway,
    "Assay": NS.Assay,
    "Compound": NS.Compound,
    "OmicsDataset": NS.OmicsDataset,
    "Publication": NS.Publication,
    "Measurement": NS.Measurement,
    "AnalyticalMethod": NS.AnalyticalMethod,
    "Result": NS.Result,
    "Organization": NS.Organization,
}

# BAO alignment: map our local classes → BAO parent class URIs
BAO_CLASS_ALIGNMENT = {
    "Assay":        BAO["BAO_0000015"],   # bioassay
    "Compound":     BAO["BAO_0000019"],   # perturbagen
    "OmicsDataset": BAO["BAO_0003114"],   # biology
    "Pathway":      OBO["GO_0008150"],    # biological_process (referenced in BAO)
    "Target":       BAO["BAO_0000539"],   # molecular target (via object property context)
}

# Object properties
OP_MENTIONED_IN_DOCUMENT = NS.mentionedInDocument

# Allowed relation predicates for extraction
ALLOWED_RELATIONS = [
    "testsTarget", "testsCompound", "involvesPathway", "relatedToPathway", 
    "actsAsAgonistFor", "bindsToProtein", "inhibits", "upregulates", "downregulates", "interactsWith",
    "sameBiologicalEntityAs", "has_assay_endpoint", "measures", "measuresAnalyte",
    "usesChallengeAgent", "hasReadoutMolecule", "hasMember",
    "developedBy", "sponsoredBy", "hasSubsidiary", "licensedFrom"
]

# Domain / Range for object properties (for WebProtégé compatibility)
PROPERTY_SIGNATURES = {
    "mentionedInDocument":("Publication", None),   # domain=Publication, range=any
    "testsTarget":      ("Assay",      "Target"),
    "testsCompound":    ("Assay",      "Compound"),
    "involvesPathway":  ("Assay",      "Pathway"),
    "relatedToPathway": (("Target", "Compound"), "Pathway"),
    "actsAsAgonistFor": ("Compound",   "Target"),
    "bindsToProtein":   ("Compound",   "Target"),
    "inhibits":         ("Compound",   "Target"),
    "upregulates":      (("Target", "Compound"), "Pathway"),
    "downregulates":    (("Target", "Compound"), "Pathway"),
    "interactsWith":    (None,         None),
    "sameBiologicalEntityAs": (None,   None),
    "has_assay_endpoint":("Assay",     "Measurement"),
    "measures":         (("Assay", "AnalyticalMethod"), "Measurement"),
    "measuresAnalyte":  (("Measurement", "AnalyticalMethod"), "Compound"),
    "usesChallengeAgent": ("Assay",    "Compound"),
    "hasReadoutMolecule": ("Assay",    "Compound"),
    "hasResult":        ("Assay",      "Result"),
    "forCompound":      ("Result",     "Compound"),
    "forTarget":        ("Result",     "Target"),
    "hasMember":        ("Compound",   "Compound"),
    "developedBy":      ("Compound",   "Organization"),
    "sponsoredBy":      (("Compound", "Assay"), "Organization"),
    "hasSubsidiary":    ("Organization","Organization"),
    "licensedFrom":     ("Organization","Organization"),
}

# Data properties
DP_LABEL = RDFS.label
DP_MENTIONED_IN = NS.mentionedInText
DP_PMID = NS.pmid
DP_NORMALIZED_NAME = NS.normalizedName
DP_TITLE = NS.title
OBO = Namespace("http://www.geneontology.org/formats/oboInOwl#")
DP_DB_XREF = OBO.hasDbXref
DP_HAS_ASSAY_DESIGN = NS.hasAssayDesign
DP_HAS_DETECTION_TECHNOLOGY = NS.hasDetectionTechnology
DP_HAS_VALUE = NS.hasValue
DP_HAS_UNIT = NS.hasUnit
DP_HAS_METRIC_TYPE = NS.hasMetricType
DP_HAS_MODALITY = NS.hasModality
DP_HAS_DEVELOPMENT_STAGE = NS.hasDevelopmentStage
DP_HAS_DEVELOPMENT_CODE = NS.hasDevelopmentCode
DP_HAS_PROVENANCE = NS.hasProvenance
DP_HAS_PATENT_NUMBER = NS.hasPatentNumber
DP_HAS_EXPIRATION_DATE = NS.hasExpirationDate
DP_EXTRACTION_METHOD = NS.extractionMethod

ENTITY_CATEGORIES = {"Target", "Pathway", "Assay", "Compound", "OmicsDataset", "Measurement", "AnalyticalMethod", "Organization"}

CATEGORY_TO_CLASS = {
    "Target": "Target",
    "Pathway": "Pathway",
    "Assay": "Assay",
    "Compound": "Compound",
    "Omics mention": "OmicsDataset",
    "OmicsDataset": "OmicsDataset",
    "Measurement": "Measurement",
    "AnalyticalMethod": "AnalyticalMethod",
    "Organization": "Organization",
}

NODE_COLORS = {
    "Target": "#4C78A8",
    "Pathway": "#F58518",
    "Assay": "#E45756",
    "Compound": "#72B7B2",
    "OmicsDataset": "#B279A2",
    "Publication": "#54A24B",
    "Measurement": "#F28E2B",
    "AnalyticalMethod": "#E15759",
    "Organization": "#FF9D9A",
    "Result": "#59A14F",
}


# ---------------------------------------------------------------------------
# NCBI link generation
# ---------------------------------------------------------------------------

def generate_db_link(identifier: str | None, name: str, category: str) -> str | None:
    """Generate a clickable database link for an entity."""
    if identifier and identifier.lower() != "null":
        curie = identifier.strip()
        if ":" in curie:
            prefix, accession = curie.split(":", 1)
            prefix_upper = prefix.upper()
            if prefix_upper == "CHEBI":
                return f"https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:{accession}"
            elif prefix_upper == "GO":
                return f"https://amigo.geneontology.org/amigo/term/GO:{accession}"
            elif prefix_upper in ("NCBIGENE", "GENEID"):
                return f"https://www.ncbi.nlm.nih.gov/gene/{accession}"
            elif prefix_upper == "UNIPROT":
                return f"https://www.uniprot.org/uniprot/{accession}"
            elif prefix_upper == "PUBCHEM":
                return f"https://pubchem.ncbi.nlm.nih.gov/compound/{accession}"
            elif prefix_upper == "MESH":
                return f"https://www.ncbi.nlm.nih.gov/mesh/{accession}"
            elif prefix_upper == "NCBITAXON":
                return f"https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id={accession}"
            else:
                return f"https://identifiers.org/{curie}"

    search_term = name.replace(" ", "%20")
    try:
        if category == "Target":
            res = requests.get(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gene&term={search_term}[gene]&retmode=json", timeout=2)
            if res.status_code == 200:
                id_list = res.json().get("esearchresult", {}).get("idlist", [])
                if id_list:
                    return f"https://www.ncbi.nlm.nih.gov/gene/{id_list[0]}"
        elif category == "Compound":
            res = requests.get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{search_term}/cids/JSON", timeout=2)
            if res.status_code == 200 and "IdentifierList" in res.json():
                cid = res.json()["IdentifierList"]["CID"][0]
                return f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}"
    except Exception:
        pass
        
    return f"https://www.ncbi.nlm.nih.gov/search/all/?term={search_term}"


# ---------------------------------------------------------------------------
# BAO reference ontology loader
# ---------------------------------------------------------------------------

BAO_OWL_PATH = Path(__file__).parent / "bao_complete.owl"


@st.cache_resource(show_spinner="Loading BAO reference ontology…")
def load_bao_labels() -> dict[str, URIRef]:
    """
    Parse bao_complete.owl and extract rdfs:label → URI mappings for BAO classes.
    Cached once per Streamlit server lifetime.
    Returns a dict: { lowercase_label: URIRef }.
    """
    mapping: dict[str, URIRef] = {}
    if not BAO_OWL_PATH.exists():
        return mapping

    try:
        g = Graph()
        g.parse(str(BAO_OWL_PATH), format="xml")

        # Collect all classes with rdfs:label
        for subj, _, label in g.triples((None, RDFS.label, None)):
            if isinstance(subj, URIRef) and isinstance(label, Literal):
                label_str = str(label).strip().lower()
                if label_str and "bioassayontology" in str(subj):
                    mapping[label_str] = subj
    except Exception:
        # If BAO parsing fails, degrade gracefully — use static alignment only
        pass

    return mapping


# ---------------------------------------------------------------------------
# Document text extraction (multi-format)
# ---------------------------------------------------------------------------


def extract_text_from_file(uploaded_file) -> str:
    """Extract text content from an uploaded file."""
    uploaded_file.seek(0)
    name = uploaded_file.name.lower()
    ext = Path(name).suffix

    if ext in (".txt", ".md"):
        return uploaded_file.read().decode("utf-8", errors="replace")

    elif ext == ".pdf":
        if fitz is None:
            raise ImportError("PyMuPDF is required to read PDF files. Run: pip install PyMuPDF")
        
        # Read the file bytes into fitz
        file_bytes = uploaded_file.read()
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        
        pages = []
        for page in doc:
            text = page.get_text("text")
            if text:
                pages.append(text.strip())
        doc.close()
        return "\n\n".join(pages) if pages else "(No text extracted from PDF)"

    elif ext == ".docx":
        if DocxDocument is None:
            raise ImportError("python-docx is required to read DOCX files. Run: pip install python-docx")
        doc = DocxDocument(io.BytesIO(uploaded_file.read()))
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs) if paragraphs else "(No text extracted from DOCX)"

    elif ext == ".csv":
        df = pd.read_csv(io.BytesIO(uploaded_file.read()))
        return df.to_string(index=False)

    elif ext == ".xlsx":
        df = pd.read_excel(io.BytesIO(uploaded_file.read()), engine="openpyxl")
        return df.to_string(index=False)

    elif ext == ".json":
        raw = uploaded_file.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(raw)
            return json.dumps(data, indent=2)
        except json.JSONDecodeError:
            return raw

    elif ext == ".xml":
        return uploaded_file.read().decode("utf-8", errors="replace")

    else:
        # Fallback: try to read as text
        return uploaded_file.read().decode("utf-8", errors="replace")


# ---------------------------------------------------------------------------
# Extraction prompt
# ---------------------------------------------------------------------------

EXTRACTION_PROMPT = """You are a deterministic entity and relation extraction compiler for biomedical abstracts.

Extract ONLY entities explicitly mentioned in the text below. Do NOT infer or hallucinate.
Separate compound concepts: e.g., "MetforminPharmacogenetics" should be extracted as two distinct entities: "Metformin" (Compound) and "Pharmacogenetics" (OmicsDataset), linked by a relationship.

Categories (use exactly these):
- Target: receptors, enzymes, or ion channels explicitly named that are being screened against. IMPORTANT: If it is an endogenous molecule or synthesized analog being evaluated in an assay, classify as Compound, NOT Target.
- Pathway: biological pathways or biological processes
- Assay: Real bioassay formats testing biological activity (e.g., ReceptorBindingAssay). IMPORTANT: When multiple assay-related phrases describe ONE experiment, consolidate them into ONE Assay entity with facets.
- Measurement: Measured endpoints/outcomes of a study (e.g., BloodGlucose, BindingAffinity). Model as: Assay has_assay_endpoint Measurement.
- AnalyticalMethod: Analytical/characterization methods that confirm identity/purity (e.g., HPLC, RP-HPLC, NMR, LC/MS).
- Compound: drugs, small molecules, tool compounds, challenge agents, readout molecules, endogenous ligands, or synthesized analogs (e.g., Peptides, Incretins) being evaluated.
- OmicsDataset: omics methods or datasets (e.g., RNA-seq, proteomics)
- Organization: corporate sponsors, competitors, academic institutions, subsidiaries, or licensors (e.g., Pfizer, Genentech, Harvard University).

Extract biological relationships between the extracted entities using ONLY the following allowed predicates:
["testsTarget", "testsCompound", "involvesPathway", "relatedToPathway", "actsAsAgonistFor", "bindsToProtein", "inhibits", "upregulates", "downregulates", "interactsWith", "sameBiologicalEntityAs", "has_assay_endpoint", "measures", "measuresAnalyte", "usesChallengeAgent", "hasReadoutMolecule", "hasMember", "developedBy", "sponsoredBy", "hasSubsidiary", "licensedFrom"]

CRITICAL PROPERTY USAGE RULES:
- `testsCompound`: ONLY for the actual therapeutic/test compound whose efficacy is being evaluated.
- `actsAsAgonistFor` / `bindsToProtein`: Connect a Compound to a Target protein it binds or acts upon.
- `usesChallengeAgent`: For provocation substances (e.g., Glucose injected in a tolerance test).
- `hasReadoutMolecule`: For measured signal molecules (e.g., cAMP in a functional assay).
- `hasMember`: Connect a drug class node (e.g., GLP1ReceptorAgonists) to its specific members (e.g., Semaglutide or SEQ ID NO 15). DO NOT merge a drug class and its member into a single string (e.g., NEVER output 'GLP1ReceptorAgonist_SEQIDNO15'). You must extract them as TWO distinct entities and connect them using `hasMember`.
- `sameBiologicalEntityAs`: Connect two entities if they are the exact same biological molecule acting in different roles.
- `developedBy`: Connect a Compound to the Organization that developed it. Example: "Pfizer developed Semaglutide" -> Semaglutide developedBy Pfizer.
- `sponsoredBy`: Connect an Assay or Compound to its sponsoring Organization. Example: "The trial was sponsored by Genentech" -> Trial sponsoredBy Genentech.
- `hasSubsidiary`: Connect an Organization to its subsidiary Organization. Example: "Lilly Research Laboratories, a division of Eli Lilly" -> Eli Lilly hasSubsidiary Lilly Research Laboratories.
- `licensedFrom`: Connect an Organization to the Organization it licensed a compound from.

Provide a canonical CURIE identifier for entities if possible (e.g., CHEBI:6801, NCBITaxon:9606, GO:0008150), else return null.

Return valid JSON ONLY — no markdown, no commentary. Schema:

{
  "document_metadata": {
    "patentNumber": "Extract ONLY if the number identifies this document itself (e.g., stated in a title/header context). NEVER extract patent numbers cited within the body as prior art. Example YES: 'U.S. Pat. No. 9,884,093' in the header. Example NO: 'as described in U.S. Pat. 5,123,456' in the body text.",
    "expirationDate": "Extract if present for the document itself",
    "provenance": "Extract if explicitly stated source provenance"
  },
  "entities": [
    {
      "text": "exact span from the abstract",
      "category": "Target|Pathway|Assay|Measurement|AnalyticalMethod|Compound|OmicsDataset|Organization",
      "normalized_name": "ShortReadableName",
      "identifier": "CHEBI:123 or null",
      "design": "assay design if Assay",
      "technology": "detection tech if Assay",
      "modality": "Compound modality. MUST BE ONE OF: Small Molecule, Peptide, Fusion Protein, Biologic, Monoclonal Antibody, siRNA, CRISPR Gene Editing, CAR-T, Other",
      "developmentStage": "Compound stage. MUST BE ONE OF: Target Validation, Hit to Lead, Lead Optimization, Preclinical, Phase 1, Phase 2, Phase 3, Approved, Other",
      "developmentCode": "Asset ID/Development code if Compound (e.g., PF-0123)"
    }
  ],
  "relationships": [
    {
      "source": "NormalizedNameOfSource",
      "predicate": "testsTarget",
      "target": "NormalizedNameOfTarget",
      "result": {
        "value": 15,
        "unit": "nM",
        "metricType": "Exact BAO metric type (e.g. EC50, IC50, Ki, Kd, Emax). Do not blend detection technology (like GTPyS) into this string."
      }
    },
    {
      "source": "EliLilly",
      "predicate": "hasSubsidiary",
      "target": "LillyResearchLaboratories"
    }
  ]
}

If no entities are found, return: {"document_metadata": {}, "entities": [], "relationships": []}

CRITICAL — MANDATORY QUANTITATIVE RESULT EXTRACTION:
Every assay endpoint with a reported number MUST produce a "result" object on the corresponding relationship. Naming the measurement type via has_assay_endpoint (e.g., "this assay measures Ki") is NOT a substitute for the actual reported value. Both must be present together: the Measurement entity describes the endpoint category; the "result" object carries the specific number from the text.

For every relationship whose source is an Assay (or Compound tested by an Assay) and where the source text reports a specific numeric outcome (e.g., Ki = 15 nM, EC50 = 3.2 nM, half-life = 7.1 h, AUC = 1500 ng·h/mL, body weight change = -12%), you MUST include a "result" object with:
- "value": the numeric value (as a JSON number, NOT a string)
- "unit": the unit of measurement (e.g., "nM", "h", "mg/kg", "%")
- "metricType": the metric name as a plain string (e.g., "Ki", "EC50", "AUC", "Half-life", "Cmax"). Use the human-readable label, NOT a BAO term ID.

Self-check before returning: Count the assays/endpoints in the document that report specific numbers. Count the "result" objects in your output. If the document clearly reports pharmacokinetic parameters (half-life, Cmax, Tmax, AUC, clearance), binding affinities (Ki, IC50, EC50, Kd), or in vivo outcomes (body weight, blood glucose, food intake) as numbers, and your output contains ZERO "result" objects, STOP — you have missed the quantitative data. Go back to the source text for each assay and extract the reported values before returning.

Do NOT hallucinate quantitative values if the text doesn't state one. Only include "result" objects when the text explicitly reports a number. Do NOT include optional properties like "modality" unless relevant information is present in the text.

Extract ONLY entities mentioned in the <document> block below.

<document>
"""


# ---------------------------------------------------------------------------
# PubMed helpers
# ---------------------------------------------------------------------------

def parse_pmid(raw: str) -> str | None:
    """Extract PMID from raw input (digits, URL, or pubmed.ncbi.nlm.nih.gov link)."""
    raw = raw.strip()
    if not raw:
        return None
    if raw.isdigit():
        return raw
    if "pubmed" in raw.lower() or raw.startswith("http"):
        match = re.search(r"/(\d{5,9})(?:/|$|\?|#)", raw)
        if match:
            return match.group(1)
        match = re.search(r"(\d{5,9})", raw)
        if match:
            return match.group(1)
    match = re.search(r"(\d{5,9})", raw)
    return match.group(1) if match else None


def fetch_pubmed(pmid: str, api_key: str | None = None) -> dict[str, str]:
    """Fetch title and abstract via NCBI esummary + efetch."""
    params_base: dict[str, str] = {"db": "pubmed", "id": pmid, "retmode": "json"}
    if api_key:
        params_base["api_key"] = api_key

    summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    summary_resp = requests.get(summary_url, params=params_base, timeout=30)
    summary_resp.raise_for_status()
    summary_data = summary_resp.json()
    result = summary_data.get("result", {})
    if pmid not in result:
        raise ValueError(f"PMID {pmid} not found in PubMed.")
    record = result[pmid]
    title = record.get("title", "").strip()
    if record.get("error"):
        raise ValueError(record["error"])

    fetch_params: dict[str, str] = {
        "db": "pubmed",
        "id": pmid,
        "retmode": "xml",
    }
    if api_key:
        fetch_params["api_key"] = api_key

    fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    fetch_resp = requests.get(fetch_url, params=fetch_params, timeout=30)
    fetch_resp.raise_for_status()

    abstract = _parse_abstract_from_xml(fetch_resp.text)
    if not abstract:
        abstract = "(No abstract available for this record.)"

    return {"pmid": pmid, "title": title, "abstract": abstract}


def _parse_abstract_from_xml(xml_text: str) -> str:
    """Minimal XML abstract extraction without lxml dependency."""
    parts: list[str] = []
    for match in re.finditer(r"<AbstractText[^>]*>(.*?)</AbstractText>", xml_text, re.DOTALL):
        text = re.sub(r"<[^>]+>", "", match.group(1)).strip()
        if text:
            parts.append(text)
    return " ".join(parts)


# ---------------------------------------------------------------------------
# LLM entity extraction (Databricks Foundation Model API)
# ---------------------------------------------------------------------------

DEFAULT_DATABRICKS_HOST = "https://dbc-8b632c81-463a.cloud.databricks.com"
DEFAULT_DATABRICKS_MODEL = "system.ai.gpt-5-5-pro"


def _strip_json_fence(raw: str) -> str:
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return raw.strip()


def _parse_extraction_response(raw: str) -> dict[str, Any]:
    data = json.loads(_strip_json_fence(raw))
    entities = data.get("entities", [])
    relationships = data.get("relationships", [])
    document_metadata = data.get("document_metadata", {})

    cleaned_entities = []
    for ent in entities:
        if not isinstance(ent, dict):
            continue
        category = ent.get("category", "")
        if category == "Omics mention":
            category = "OmicsDataset"
        if category not in ENTITY_CATEGORIES:
            continue
            
        cleaned_ent = {
            "text": str(ent.get("text", "")).strip(),
            "category": category,
            "normalized_name": str(ent.get("normalized_name", ent.get("text", ""))).strip(),
            "identifier": str(ent.get("identifier", "")).strip() if ent.get("identifier") else None,
        }
        
        for f_key in ["design", "technology", "modality", "developmentStage", "developmentCode"]:
            if f_key in ent:
                cleaned_ent[f_key] = str(ent[f_key]).strip()
        cleaned_entities.append(cleaned_ent)

    cleaned_rels = []
    for rel in relationships:
        if not isinstance(rel, dict):
            continue
        pred = rel.get("predicate", "")
        if pred not in ALLOWED_RELATIONS:
            continue
            
        cleaned_rel = {
            "source": str(rel.get("source", "")).strip(),
            "predicate": pred,
            "target": str(rel.get("target", "")).strip(),
        }
        
        if "result" in rel and isinstance(rel["result"], dict):
            cleaned_rel["result"] = {
                "value": rel["result"].get("value"),
                "unit": str(rel["result"].get("unit", "")).strip(),
                "metricType": str(rel["result"].get("metricType", "")).strip()
            }
            
        cleaned_rels.append(cleaned_rel)

    return {"document_metadata": document_metadata, "entities": cleaned_entities, "relationships": cleaned_rels}


def call_databricks_chat(
    host: str,
    token: str,
    model: str,
    prompt: str,
    max_tokens: int = 16384,
) -> str:
    """
    Query a Databricks serving endpoint via the OpenAI-compatible chat API.
    Falls back to direct /serving-endpoints/{model}/invocations if needed.
    """
    host = host.rstrip("/")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    messages = [{"role": "user", "content": prompt}]

    # Custom payload format provided in the curl
    ai_gw_input = [
        {
            "role": "user",
            "content": [{"type": "input_text", "text": prompt}]
        }
    ]

    payloads = [
        (
            f"{host}/serving-endpoints/chat/completions",
            {"model": model, "messages": messages, "max_tokens": max_tokens},
        ),
        (
            f"{host}/serving-endpoints/{model}/invocations",
            {"messages": messages, "max_tokens": max_tokens},
        ),
        (
            f"{host}/ai-gateway/openai/v1/chat/completions",
            {"model": model, "messages": messages, "max_tokens": max_tokens},
        ),
        (
            f"{host}/ai-gateway/mlflow/v1/chat/completions",
            {"model": model, "messages": messages, "max_tokens": max_tokens},
        ),
        (
            f"{host}/ai-gateway/openai/v1/responses",
            {"model": model, "input": ai_gw_input, "max_output_tokens": max_tokens},
        ),
    ]

    last_error = "Unknown Databricks API error."
    for url, payload in payloads:
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=600)
            if resp.status_code == 404:
                last_error = f"Endpoint not found at {url}"
                continue
            if not resp.ok:
                detail = resp.text[:500]
                if resp.status_code == 403 and "model-serving" in detail:
                    last_error = (
                        "Databricks token missing required scope: model-serving. "
                        "Create a new personal access token in Databricks with the "
                        "'model-serving' scope enabled, then update your API token."
                    )
                    continue
                last_error = f"Databricks API {resp.status_code}: {detail}"
                continue
            data = resp.json()
            content = _extract_chat_content(data)
            if content:
                return content
            last_error = f"Empty response from {url}: {json.dumps(data)[:2000]}"
        except RuntimeError:
            raise
        except requests.RequestException as exc:
            last_error = f"Request to {url} failed: {exc}"

    raise RuntimeError(last_error)


def _extract_chat_content(data: dict[str, Any]) -> str:
    """Parse assistant text from OpenAI-compatible or Databricks invocation payloads."""
    choices = data.get("choices") or []
    if choices:
        choice = choices[0]
        if "message" in choice:
            content = choice["message"].get("content", "")
            if isinstance(content, list):
                content = "".join(
                    part.get("text", "") if isinstance(part, dict) else str(part) for part in content
                )
            if str(content).strip():
                return str(content)
        if "text" in choice and str(choice["text"]).strip():
            return str(choice["text"])

    for key in ("predictions", "outputs", "candidates", "output", "response", "responses"):
        items = data.get(key)
        if isinstance(items, list) and items:
            for item in items:
                if isinstance(item, str) and item.strip():
                    return item
                if isinstance(item, dict):
                    if "content" in item and isinstance(item["content"], list):
                        parts = item["content"]
                        for part in parts:
                            if isinstance(part, dict) and "text" in part:
                                text = part.get("text", "")
                                if text:
                                    return str(text)
                    if "content" in item and isinstance(item["content"], dict):
                        parts = item["content"].get("parts", [])
                        if isinstance(parts, list) and parts:
                            text = parts[0].get("text", "")
                            if text:
                                return str(text)
                    for subkey in ("content", "text", "generated_text", "output"):
                        val = item.get(subkey)
                        if isinstance(val, str) and val.strip():
                            return val
                        if isinstance(val, list) and val:
                            extracted = _extract_chat_content({"choices": [{"message": {"content": val}}]})
                            if extracted:
                                return extracted

    if isinstance(data.get("content"), str) and data["content"].strip():
        return data["content"]

    # Generic fallback: look for ANY string that looks like JSON response
    for k, v in data.items():
        if isinstance(v, str) and len(v) > 50 and '{' in v:
            return v

    return ""


def extract_entities(
    text: str,
    databricks_host: str,
    databricks_token: str,
    databricks_model: str = DEFAULT_DATABRICKS_MODEL,
    max_retries: int = 2,
) -> tuple[dict[str, list], str | None]:
    """Call Databricks Foundation Model API with retry; return (extraction_data, error_message)."""
    empty_res = {"entities": [], "relationships": []}
    if not databricks_token:
        return empty_res, "Databricks API token is required. Configure DATABRICKS_TOKEN in .streamlit/secrets.toml"
    if not databricks_host:
        return empty_res, "Databricks workspace URL is required. Configure DATABRICKS_HOST in .streamlit/secrets.toml"
    # Close document tag
    prompt = EXTRACTION_PROMPT + text + "\n</document>"
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            raw = call_databricks_chat(
                host=databricks_host,
                token=databricks_token,
                model=databricks_model,
                prompt=prompt,
            )
            result = _parse_extraction_response(raw)
            if result.get("entities"):
                # Post-extraction validation: check for missing quantitative results
                rels = result.get("relationships", [])
                endpoint_count = sum(1 for r in rels if r.get("predicate") == "has_assay_endpoint")
                result_count = sum(1 for r in rels if isinstance(r.get("result"), dict) and r["result"].get("value") is not None)
                if endpoint_count > 0 and result_count == 0:
                    result["_validation_warning"] = (
                        f"⚠️ Potential missing results: {endpoint_count} assay endpoint(s) "
                        f"found but 0 quantitative Result objects extracted. "
                        f"The source document may contain numeric data that was not captured. "
                        f"Consider re-running extraction or reviewing the source text."
                    )
                return result, None
            # Got valid JSON but no entities — might be a weak response, retry
            last_error = "LLM returned valid JSON but extracted 0 entities."
            if attempt < max_retries:
                time.sleep(2)
                continue
            return result, last_error
        except json.JSONDecodeError as exc:
            last_error = f"LLM returned malformed JSON (attempt {attempt}/{max_retries}): {exc}"
        except requests.RequestException as exc:
            last_error = f"Databricks request failed (attempt {attempt}/{max_retries}): {exc}"
        except RuntimeError as exc:
            last_error = f"Databricks API error (attempt {attempt}/{max_retries}): {exc}"
        except Exception as exc:
            last_error = f"Entity extraction failed (attempt {attempt}/{max_retries}): {exc}"

        if attempt < max_retries:
            time.sleep(2)  # Brief pause before retry

    return empty_res, f"{last_error}"


# ---------------------------------------------------------------------------
# Ontology / graph construction — WebProtégé compatible OWL
# ---------------------------------------------------------------------------

def slugify(name: str) -> str:
    """Create a URI-safe slug from a normalized entity name."""
    slug = re.sub(r"[^A-Za-z0-9]+", "_", name.strip())
    slug = slug.strip("_")
    return slug or "Unknown"


def init_tbox(g: Graph, bao_labels: dict[str, URIRef]) -> None:
    """Define TBox with proper OWL declarations for WebProtégé."""
    g.bind("ao", NS)
    g.bind("owl", OWL)
    g.bind("rdfs", RDFS)
    g.bind("xsd", XSD)
    g.bind("bao", BAO)
    g.bind("obo", OBO)

    # ── Ontology declaration (required by WebProtégé) ──
    ont_uri = URIRef(ONTOLOGY_IRI)
    g.add((ont_uri, RDF.type, OWL.Ontology))
    g.add((ont_uri, RDFS.label, Literal("Assay-Centric Ontology")))
    g.add((ont_uri, OWL.versionInfo, Literal("2.0")))
    # Import BAO reference
    g.add((ont_uri, OWL.imports, URIRef("http://www.bioassayontology.org/bao/bao_complete.owl")))

    # ── Class declarations ──
    for label, uri in CLASS_URIS.items():
        g.add((uri, RDF.type, OWL.Class))
        g.add((uri, RDFS.label, Literal(label)))

        # BAO alignment: declare subClassOf relationship to BAO parent
        bao_parent = BAO_CLASS_ALIGNMENT.get(label)
        if bao_parent:
            g.add((uri, RDFS.subClassOf, bao_parent))

    # ── Object property declarations with domain/range ──
    for rel_name, (domain_cls, range_cls) in PROPERTY_SIGNATURES.items():
        prop_uri = NS[rel_name]
        g.add((prop_uri, RDF.type, OWL.ObjectProperty))
        g.add((prop_uri, RDFS.label, Literal(rel_name)))
        if domain_cls:
            if isinstance(domain_cls, tuple):
                union_node = BNode()
                list_node = BNode()
                g.add((union_node, RDF.type, OWL.Class))
                g.add((union_node, OWL.unionOf, list_node))
                from rdflib.collection import Collection
                Collection(g, list_node, [CLASS_URIS[d] for d in domain_cls if d in CLASS_URIS])
                g.add((prop_uri, RDFS.domain, union_node))
            elif domain_cls in CLASS_URIS:
                g.add((prop_uri, RDFS.domain, CLASS_URIS[domain_cls]))
        if range_cls:
            if isinstance(range_cls, tuple):
                union_node = BNode()
                list_node = BNode()
                g.add((union_node, RDF.type, OWL.Class))
                g.add((union_node, OWL.unionOf, list_node))
                from rdflib.collection import Collection
                Collection(g, list_node, [CLASS_URIS[r] for r in range_cls if r in CLASS_URIS])
                g.add((prop_uri, RDFS.range, union_node))
            elif range_cls in CLASS_URIS:
                g.add((prop_uri, RDFS.range, CLASS_URIS[range_cls]))

    # ── Data property declarations ──
    for dp, dp_label in [
        (DP_PMID, "pmid"),
        (DP_TITLE, "title"),
        (DP_NORMALIZED_NAME, "normalizedName"),
        (DP_DB_XREF, "databaseLink"),
        (DP_MENTIONED_IN, "mentionedInText"),
        (DP_HAS_ASSAY_DESIGN, "hasAssayDesign"),
        (DP_HAS_DETECTION_TECHNOLOGY, "hasDetectionTechnology"),
        (DP_HAS_VALUE, "hasValue"),
        (DP_HAS_UNIT, "hasUnit"),
        (DP_HAS_METRIC_TYPE, "hasMetricType"),
        (DP_HAS_MODALITY, "hasModality"),
        (DP_HAS_DEVELOPMENT_STAGE, "hasDevelopmentStage"),
        (DP_HAS_DEVELOPMENT_CODE, "hasDevelopmentCode"),
        (DP_HAS_PROVENANCE, "hasProvenance"),
    ]:
        g.add((dp, RDF.type, OWL.DatatypeProperty))
        g.add((dp, RDFS.label, Literal(dp_label)))


def normalize_entities(extraction_data: dict[str, list]) -> None:
    """
    Deduplicates entities in extraction_data inline by merging those with highly 
    similar names (within the same category) and updating relationship text references.
    """
    import difflib
    entities = extraction_data.get("entities", [])
    if not entities:
        return
        
    normalized = []
    text_mapping = {}  # Map original entity text -> canonical normalized text
    
    for ent in entities:
        if not isinstance(ent, dict):
            continue
            
        ent_text = ent.get("text", "")
        ent_name = ent.get("normalized_name") or ent_text
        if not ent_name:
            continue
            
        ent_name_lower = ent_name.strip().lower()
        
        matched_existing = None
        for existing in normalized:
            existing_name = (existing.get("normalized_name") or existing.get("text", "")).strip().lower()
            
            # Merge if same category and highly similar string (or identical identifier)
            if existing.get("category") == ent.get("category"):
                if ent_name_lower == existing_name or difflib.SequenceMatcher(None, ent_name_lower, existing_name).ratio() > 0.85:
                    matched_existing = existing
                    break
                elif ent.get("identifier") and existing.get("identifier") and ent["identifier"] == existing["identifier"]:
                    matched_existing = existing
                    break
                    
        if matched_existing:
            # Upgrade identifier if new has it and existing doesn't
            if ent.get("identifier") and not matched_existing.get("identifier"):
                matched_existing["identifier"] = ent["identifier"]
                
            # Map the original text span to the merged text span so edges can find it
            if ent_text:
                text_mapping[ent_text] = matched_existing.get("text", ent_text)
        else:
            normalized.append(ent)
            if ent_text:
                text_mapping[ent_text] = ent_text
                
    extraction_data["entities"] = normalized
    
    # Update relationships to point to the canonical text span
    for rel in extraction_data.get("relationships", []):
        if rel.get("source") in text_mapping:
            rel["source"] = text_mapping[rel["source"]]
        if rel.get("target") in text_mapping:
            rel["target"] = text_mapping[rel["target"]]

def build_ontology(
    extraction_data: dict[str, list],
    title: str,
    pmid: str | None,
    text: str,
    bao_labels: dict[str, URIRef],
) -> Graph:
    """Build in-memory OWL graph (TBox + ABox) from extracted entities.
    
    Produces WebProtégé-compatible output with:
    - owl:Ontology declaration
    - owl:NamedIndividual types on all instances
    - rdfs:domain / rdfs:range on object properties
    - BAO class alignment via rdfs:subClassOf
    - NCBI links as data properties
    """
    g = Graph()
    init_tbox(g, bao_labels)

    # Publication Node
    pub_id = f"PMID_{pmid}" if pmid else "Document_Manual"
    pub_uri = NS[pub_id]
    g.add((pub_uri, RDF.type, OWL.NamedIndividual))
    g.add((pub_uri, RDF.type, CLASS_URIS["Publication"]))
    g.add((pub_uri, DP_LABEL, Literal(f"PMID:{pmid}" if pmid else "Document")))
    g.add((pub_uri, DP_TITLE, Literal(title or "Untitled document", datatype=XSD.string)))
    if pmid:
        g.add((pub_uri, DP_PMID, Literal(pmid, datatype=XSD.string)))
        g.add((pub_uri, DP_DB_XREF, Literal(
            f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/", datatype=XSD.anyURI)))

    patent_match = re.search(r"\b([A-Z]{2}\d{5,15}[A-Z0-9]*)\b", title, re.IGNORECASE)
    doc_metadata = extraction_data.get("document_metadata", {})
    
    if patent_match:
        g.add((pub_uri, DP_EXTRACTION_METHOD, Literal("deterministic")))
        g.add((pub_uri, DP_HAS_PROVENANCE, Literal("Patent")))
        g.add((pub_uri, DP_HAS_PATENT_NUMBER, Literal(patent_match.group(1).upper())))
        if doc_metadata.get("expirationDate") and not doc_metadata["expirationDate"].startswith("Extract"):
            g.add((pub_uri, DP_HAS_EXPIRATION_DATE, Literal(doc_metadata["expirationDate"])))
    elif pmid:
        g.add((pub_uri, DP_EXTRACTION_METHOD, Literal("deterministic")))
        g.add((pub_uri, DP_HAS_PROVENANCE, Literal("PubMed")))
    elif doc_metadata:
        g.add((pub_uri, DP_EXTRACTION_METHOD, Literal("llm")))
        if doc_metadata.get("patentNumber") and not doc_metadata["patentNumber"].startswith("Extract"):
            g.add((pub_uri, DP_HAS_PATENT_NUMBER, Literal(doc_metadata["patentNumber"])))
        if doc_metadata.get("expirationDate") and not doc_metadata["expirationDate"].startswith("Extract"):
            g.add((pub_uri, DP_HAS_EXPIRATION_DATE, Literal(doc_metadata["expirationDate"])))
            
    if doc_metadata.get("provenance") and not doc_metadata["provenance"].startswith("Extract"):
        if not (patent_match or pmid):
            g.add((pub_uri, DP_HAS_PROVENANCE, Literal(doc_metadata["provenance"])))

    entities = extraction_data.get("entities", [])
    relationships = extraction_data.get("relationships", [])

    name_to_uri: dict[str, URIRef] = {}
    class_norm_to_uri: dict[tuple[str, str], URIRef] = {}
    class_id_to_uri: dict[tuple[str, str], URIRef] = {}
    global_norm_to_uri: dict[str, URIRef] = {}
    global_id_to_uri: dict[str, URIRef] = {}
    seen_slugs: set[str] = set()

    target_names = {rel.get("target") for rel in relationships if isinstance(rel, dict) and rel.get("target")}

    for ent in entities:
        cls_name = CATEGORY_TO_CLASS.get(ent["category"])
        if not cls_name:
            continue

        norm_name = ent["normalized_name"]
        identifier = ent.get("identifier")
        if identifier and identifier.lower() == "null":
            identifier = None

        text = ent.get("text", "").strip()
        text = re.sub(r"\s+-\s+", "-", text)

        existing_uri = class_norm_to_uri.get((cls_name, norm_name))
        if not existing_uri and identifier:
            existing_uri = class_id_to_uri.get((cls_name, identifier))

        if existing_uri:
            if text:
                g.add((existing_uri, DP_MENTIONED_IN, Literal(text)))
            for f_key, dp in [("design", DP_HAS_ASSAY_DESIGN), ("technology", DP_HAS_DETECTION_TECHNOLOGY),
                              ("modality", DP_HAS_MODALITY), ("developmentStage", DP_HAS_DEVELOPMENT_STAGE),
                              ("developmentCode", DP_HAS_DEVELOPMENT_CODE)]:
                val = ent.get(f_key)
                if val and not str(val).startswith("Compound"):
                    g.add((existing_uri, dp, Literal(val)))
            name_to_uri[norm_name] = existing_uri
            continue

        base_slug = f"{cls_name}_{slugify(norm_name)}"
        slug = base_slug
        counter = 2
        while slug in seen_slugs:
            slug = f"{base_slug}_{counter}"
            counter += 1
        seen_slugs.add(slug)

        ind_uri = NS[slug]
        name_to_uri[norm_name] = ind_uri
        class_norm_to_uri[(cls_name, norm_name)] = ind_uri
        if identifier:
            class_id_to_uri[(cls_name, identifier)] = ind_uri

        cross_uri = global_norm_to_uri.get(norm_name)
        if not cross_uri and identifier:
            cross_uri = global_id_to_uri.get(identifier)
        
        if cross_uri:
            g.add((ind_uri, NS.sameBiologicalEntityAs, cross_uri))
            g.add((cross_uri, NS.sameBiologicalEntityAs, ind_uri))
            
        global_norm_to_uri[norm_name] = ind_uri
        if identifier:
            global_id_to_uri[identifier] = ind_uri

        g.add((ind_uri, RDF.type, OWL.NamedIndividual))
        g.add((ind_uri, RDF.type, CLASS_URIS[cls_name]))
        g.add((ind_uri, DP_LABEL, Literal(norm_name)))
        g.add((ind_uri, DP_NORMALIZED_NAME, Literal(norm_name)))

        if identifier:
            g.add((ind_uri, DP_DB_XREF, Literal(identifier)))

        if text:
            g.add((ind_uri, DP_MENTIONED_IN, Literal(text)))

        for f_key, dp in [("design", DP_HAS_ASSAY_DESIGN), ("technology", DP_HAS_DETECTION_TECHNOLOGY),
                          ("modality", DP_HAS_MODALITY), ("developmentStage", DP_HAS_DEVELOPMENT_STAGE),
                          ("developmentCode", DP_HAS_DEVELOPMENT_CODE)]:
            val = ent.get(f_key)
            if val and not str(val).startswith("Compound"):
                g.add((ind_uri, dp, Literal(val)))

        db_link = generate_db_link(identifier, norm_name, ent["category"])
        if db_link:
            g.add((ind_uri, DP_DB_XREF, Literal(db_link, datatype=XSD.anyURI)))

        bao_match = bao_labels.get(norm_name.lower())
        if bao_match:
            g.add((ind_uri, DP_DB_XREF, Literal(str(bao_match))))

        if norm_name not in target_names:
            g.add((pub_uri, OP_MENTIONED_IN_DOCUMENT, ind_uri))

    result_counter = 1
    for rel in relationships:
        src_uri = name_to_uri.get(rel["source"])
        tgt_uri = name_to_uri.get(rel["target"])
        if src_uri and tgt_uri:
            if src_uri == tgt_uri:
                continue
                
            pred_name = rel["predicate"]
            if pred_name == "has_assay_endpoint":
                if "AnalyticalMethod" in str(src_uri):
                    prop_uri = NS["measuresAnalyte"]
                else:
                    prop_uri = NS["has_assay_endpoint"]
            elif pred_name == "measures":
                if "AnalyticalMethod" in str(src_uri):
                    prop_uri = NS["measuresAnalyte"]
                else:
                    prop_uri = NS["measures"]
            else:
                prop_uri = NS[pred_name]
                
            g.add((src_uri, prop_uri, tgt_uri))

            if "result" in rel:
                res = rel["result"]
                if res.get("value") is not None:
                    res_slug = f"Result_{result_counter}"
                    result_counter += 1
                    res_uri = NS[res_slug]
                    
                    g.add((res_uri, RDF.type, OWL.NamedIndividual))
                    g.add((res_uri, RDF.type, CLASS_URIS["Result"]))
                    g.add((res_uri, DP_LABEL, Literal(res_slug)))
                    try:
                        typed_val = Literal(float(res["value"]), datatype=XSD.double)
                    except (ValueError, TypeError):
                        typed_val = Literal(res["value"], datatype=XSD.decimal)
                    g.add((res_uri, DP_HAS_VALUE, typed_val))
                    if res.get("unit"):
                        g.add((res_uri, DP_HAS_UNIT, Literal(res["unit"], datatype=XSD.string)))
                    if res.get("metricType"):
                        # hasMetricType is owl:DatatypeProperty — always emit string literal, never a BAO URI
                        g.add((res_uri, DP_HAS_METRIC_TYPE, Literal(res["metricType"], datatype=XSD.string)))
                        
                    # Ensure hasResult is only attached to Assays
                    if (src_uri, RDF.type, CLASS_URIS["Assay"]) in g:
                        g.add((src_uri, NS.hasResult, res_uri))
                        if (tgt_uri, RDF.type, CLASS_URIS["Target"]) in g:
                            g.add((res_uri, NS.forTarget, tgt_uri))
                            for cmpd in g.objects(src_uri, NS.testsCompound):
                                g.add((res_uri, NS.forCompound, cmpd))
                        elif (tgt_uri, RDF.type, CLASS_URIS["Compound"]) in g:
                            g.add((res_uri, NS.forCompound, tgt_uri))
                            for target in g.objects(src_uri, NS.testsTarget):
                                g.add((res_uri, NS.forTarget, target))
                    elif (src_uri, RDF.type, CLASS_URIS["Compound"]) in g:
                        # If a compound has a result, find the assay that tests this compound
                        for assay in g.subjects(NS.testsCompound, src_uri):
                            g.add((assay, NS.hasResult, res_uri))
                            g.add((res_uri, NS.forCompound, src_uri))
                            if (tgt_uri, RDF.type, CLASS_URIS["Target"]) in g:
                                g.add((res_uri, NS.forTarget, tgt_uri))
                            break
                        else:
                            # If no assay is found, we don't attach hasResult to the compound.
                            # Just link the result to the compound and target.
                            g.add((res_uri, NS.forCompound, src_uri))
                            if (tgt_uri, RDF.type, CLASS_URIS["Target"]) in g:
                                g.add((res_uri, NS.forTarget, tgt_uri))

    # O(N) Duplicate Removal: drop redundant aggregate edges
    from collections import defaultdict
    aggregate_to_instances = defaultdict(set)
    instance_relations = defaultdict(set)
    
    for s, p, o in g:
        if isinstance(o, URIRef):
            if p == NS.hasMember:
                aggregate_to_instances[s].add(o)
            elif p != RDF.type:
                instance_relations[s].add((p, o))
                
    edges_to_remove = []
    for agg, instances in aggregate_to_instances.items():
        for p, o in instance_relations[agg]:
            if any((p, o) in instance_relations[inst] for inst in instances):
                edges_to_remove.append((agg, p, o))
                
    for s, p, o in edges_to_remove:
        g.remove((s, p, o))

    return g


def validate_graph(g: Graph) -> list[str]:
    """Post-construction validation of the graph for domain/range consistency."""
    violations = []
    
    prop_sigs = {}
    for rel_name, (domain, range_) in PROPERTY_SIGNATURES.items():
        def resolve(c):
            if isinstance(c, tuple): return tuple(CLASS_URIS.get(x) for x in c if x in CLASS_URIS)
            return CLASS_URIS.get(c) if c else None
        prop_sigs[NS[rel_name]] = (resolve(domain), resolve(range_))
                                   
    for s, p, o in g:
        if s == o and p != NS.sameBiologicalEntityAs:
            violations.append(f"Self-reference violation: {local_name(s)} cannot have a {local_name(p)} relationship to itself.")
            
        if str(p).startswith(str(BAO)):
            violations.append(f"External property violation: BAO predicate {local_name(p)} must be mapped to a local property.")
            
        if p in prop_sigs:
            domain_cls, range_cls = prop_sigs[p]
            
            if domain_cls:
                s_types = list(g.objects(s, RDF.type))
                if isinstance(domain_cls, tuple):
                    if not any(d in s_types for d in domain_cls) and OWL.NamedIndividual in s_types:
                        allowed = " or ".join(local_name(d) for d in domain_cls if d)
                        violations.append(f"Domain violation: {local_name(s)} is subject of {local_name(p)} but is not {allowed}")
                else:
                    if domain_cls not in s_types and OWL.NamedIndividual in s_types:
                        violations.append(f"Domain violation: {local_name(s)} is subject of {local_name(p)} but is not a {local_name(domain_cls)}")
            
            if range_cls and isinstance(o, URIRef):
                o_types = list(g.objects(o, RDF.type))
                if isinstance(range_cls, tuple):
                    if not any(r in o_types for r in range_cls) and OWL.NamedIndividual in o_types:
                        allowed = " or ".join(local_name(r) for r in range_cls if r)
                        violations.append(f"Range violation: {local_name(o)} is object of {local_name(p)} but is not {allowed}")
                else:
                    if range_cls not in o_types and OWL.NamedIndividual in o_types:
                        violations.append(f"Range violation: {local_name(o)} is object of {local_name(p)} but is not a {local_name(range_cls)}")
                    
    return violations


# ---------------------------------------------------------------------------
# Graph → JSON (derived from same triples)
# ---------------------------------------------------------------------------

def local_name(uri: URIRef | BNode) -> str:
    s = str(uri)
    if "#" in s:
        return s.rsplit("#", 1)[-1]
    return s.rsplit("/", 1)[-1]


def graph_to_json(g: Graph) -> dict[str, Any]:
    """Derive UI-friendly node/edge JSON from rdflib triples."""
    class_lookup = {str(v): k for k, v in CLASS_URIS.items()}

    nodes: dict[str, dict[str, str]] = {}
    edges: list[dict[str, str]] = []
    seen_edges: set[tuple[str, str, str]] = set()

    for s, p, o in g:
        if p == RDF.type and isinstance(o, URIRef) and str(o) in class_lookup:
            nid = local_name(s)
            cls = class_lookup[str(o)]
            label = nid.replace("_", " ")
            for _, _, lit in g.triples((s, DP_LABEL, None)):
                label = str(lit)
                break

            # Append CURIE if available
            for _, _, xref in g.triples((s, DP_DB_XREF, None)):
                xref_str = str(xref)
                if not xref_str.startswith("http"):
                    label += f"\n[{xref_str}]"
                    break

            # Append Layer 3/5 metadata if available
            if cls == "Compound":
                stages = [str(x) for _, _, x in g.triples((s, DP_HAS_DEVELOPMENT_STAGE, None))]
                if stages:
                    label += f"\nStage: {', '.join(set(stages))}"
                for _, _, mod in g.triples((s, DP_HAS_MODALITY, None)):
                    label += f"\nModality: {str(mod)}"
                    break
            elif cls == "Publication":
                for _, _, pat in g.triples((s, DP_HAS_PATENT_NUMBER, None)):
                    label += f"\nPatent: {str(pat)}"
                    break
            elif cls == "Result":
                val = next((str(x) for _, _, x in g.triples((s, DP_HAS_VALUE, None))), "")
                unit = next((str(x) for _, _, x in g.triples((s, DP_HAS_UNIT, None))), "")
                metric_term = next((x for _, _, x in g.triples((s, DP_HAS_METRIC_TYPE, None))), None)
                
                metric = ""
                if metric_term:
                    if metric_term == BAO["BAO_0000188"]:
                        metric = "EC50"
                    elif metric_term == BAO["BAO_0000190"]:
                        metric = "IC50"
                    elif isinstance(metric_term, URIRef):
                        metric = local_name(metric_term)
                    else:
                        metric = str(metric_term)
                
                if val:
                    label = f"{metric} = {val} {unit}".strip()

            nodes[nid] = {"id": nid, "label": label, "type": cls}
            
            # Post-process Result to inject atomic fields
            if cls == "Result":
                if metric: nodes[nid]["metric_type"] = metric
                if unit: nodes[nid]["metric_unit"] = unit
                if val:
                    try:
                        nodes[nid]["metric_value"] = float(val)
                    except ValueError:
                        nodes[nid]["metric_value"] = val

    # Exclude basic datatype properties and schema axioms
    excluded_props = {str(RDF.type), str(DP_DB_XREF), str(RDFS.subClassOf)}

    for s, p, o in g:
        pred = str(p)
        if pred in excluded_props or not isinstance(o, URIRef):
            continue
            
        src, tgt = local_name(s), local_name(o)
        if src not in nodes or tgt not in nodes:
            continue
            
        rel = local_name(p)
        key = (src, tgt, rel)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append({"source": src, "target": tgt, "relation": rel})

    return {"nodes": list(nodes.values()), "edges": edges}


# ---------------------------------------------------------------------------
# Visualization (pyvis)
# ---------------------------------------------------------------------------

def render_pyvis_html(graph_json: dict[str, Any], height: str = "520px") -> str:
    """Build pyvis network HTML from graph JSON."""
    net = Network(height=height, width="100%", directed=True, bgcolor="#ffffff", font_color="#333333")
    net.set_options(
        """
        {
          "physics": {
            "enabled": true,
            "barnesHut": {"gravitationalConstant": -8000, "springLength": 120}
          },
          "edges": {
            "arrows": {"to": {"enabled": true, "scaleFactor": 0.5}},
            "font": {"size": 11, "align": "middle"},
            "smooth": {"type": "dynamic"}
          },
          "nodes": {"font": {"size": 14}}
        }
        """
    )

    for node in graph_json.get("nodes", []):
        ntype = node.get("type", "Unknown")
        color = NODE_COLORS.get(ntype, "#999999")
        if ntype == "Publication":
            shape = "diamond"
        elif ntype == "Result":
            shape = "box"
        else:
            shape = "dot"
            
        net.add_node(
            node["id"],
            label=f"{node['label']}\n({ntype})" if ntype != "Result" else node['label'],
            color=color,
            shape=shape,
            size=22 if ntype in ("Assay", "StudyContext", "Publication") else 14 if ntype == "Result" else 18,
        )

    for edge in graph_json.get("edges", []):
        net.add_edge(edge["source"], edge["target"], label=edge["relation"], title=edge["relation"])
    tmp_name = ""
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as tmp:
            tmp_name = tmp.name
            net.save_graph(tmp_name)
        with open(tmp_name, encoding="utf-8") as f:
            return f.read()
    finally:
        if tmp_name and os.path.exists(tmp_name):
            try:
                os.remove(tmp_name)
            except Exception:
                pass

def render_neo4j_html(graph_json: dict[str, Any], height: str = "560px") -> str:
    """Build Neo4j-style interactive graph HTML using vis-network."""
    nodes = graph_json.get("nodes", [])
    edges = graph_json.get("edges", [])
    
    vis_nodes = []
    for n in nodes:
        ntype = n.get("type", "Unknown")
        color = NODE_COLORS.get(ntype, "#999999")
        # Neo4j style: just the name
        label = n.get("label", n["id"]).split("\n")[0]
        
        vis_nodes.append({
            "id": n["id"],
            "label": label,
            "title": n.get("label", ""),
            "color": {"background": color, "border": color, "highlight": {"background": color, "border": "#333"}},
            "shape": "dot",
            "size": 25 if ntype == "Publication" else 15,
            "font": {"color": "#333", "size": 12, "face": "Inter, sans-serif"}
        })
        
    vis_edges = []
    for idx, e in enumerate(edges):
        vis_edges.append({
            "id": f"e{idx}",
            "from": e["source"],
            "to": e["target"],
            "label": e["relation"],
            "title": e["relation"],
            "arrows": "to",
            "color": {"color": "#A5ABB6", "highlight": "#333"},
            "font": {"size": 10, "align": "middle", "color": "#555", "face": "Inter, sans-serif"},
            "smooth": {"type": "dynamic"}
        })

    # Securely escape JSON to prevent HTML injection (XSS) when embedding in <script> tags
    safe_nodes = json.dumps(vis_nodes).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    safe_edges = json.dumps(vis_edges).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
        <style type="text/css">
            body {{ margin: 0; padding: 0; font-family: 'Inter', system-ui, sans-serif; }}
            #mynetwork {{
                width: 100%;
                height: {height};
                border: 1px solid #E2E8F0;
                border-radius: 0 0 6px 6px;
                background-color: #F8FAFC;
            }}
            #stats-bar {{
                padding: 10px 16px;
                background: #F1F5F9;
                border: 1px solid #E2E8F0;
                border-bottom: none;
                border-radius: 6px 6px 0 0;
                font-size: 13px;
                color: #475569;
                font-weight: 500;
                display: flex;
                justify-content: space-between;
            }}
        </style>
    </head>
    <body>
        <div id="stats-bar">
            <span>Interactive Graph View (Neo4j Style)</span>
            <span>{len(vis_nodes)} nodes / {len(vis_edges)} relationships</span>
        </div>
        <div id="mynetwork"></div>
        <script type="text/javascript">
            var nodes = new vis.DataSet({safe_nodes});
            var edges = new vis.DataSet({safe_edges});
            
            var container = document.getElementById('mynetwork');
            var data = {{ nodes: nodes, edges: edges }};
            var options = {{
                physics: {{
                    enabled: true,
                    barnesHut: {{ gravitationalConstant: -3000, springLength: 150 }}
                }},
                interaction: {{
                    hover: true,
                    zoomView: true,
                    dragView: true
                }}
            }};
            var network = new vis.Network(container, data, options);
            
            network.on("click", function (params) {{
                if (params.nodes.length > 0) {{
                    var selectedNode = params.nodes[0];
                    var connectedNodes = network.getConnectedNodes(selectedNode);
                    var allNodes = nodes.get();
                    
                    for (var i = 0; i < allNodes.length; i++) {{
                        if (allNodes[i].id === selectedNode || connectedNodes.indexOf(allNodes[i].id) !== -1) {{
                            nodes.update({{id: allNodes[i].id, color: {{opacity: 1}}}});
                        }} else {{
                            nodes.update({{id: allNodes[i].id, color: {{opacity: 0.15}}}});
                        }}
                    }}
                    
                    var connectedEdges = network.getConnectedEdges(selectedNode);
                    var allEdges = edges.get();
                    for (var i = 0; i < allEdges.length; i++) {{
                        if (connectedEdges.indexOf(allEdges[i].id) !== -1) {{
                            edges.update({{id: allEdges[i].id, color: {{opacity: 1}}}});
                        }} else {{
                            edges.update({{id: allEdges[i].id, color: {{opacity: 0.1}}}});
                        }}
                    }}
                }} else {{
                    var allNodes = nodes.get();
                    for (var i = 0; i < allNodes.length; i++) {{
                        nodes.update({{id: allNodes[i].id, color: {{opacity: 1}}}});
                    }}
                    var allEdges = edges.get();
                    for (var i = 0; i < allEdges.length; i++) {{
                        edges.update({{id: allEdges[i].id, color: {{opacity: 1}}}});
                    }}
                }}
            }});
        </script>
    </body>
    </html>
    """
    return html


def render_blue_circle_html(graph_json: dict[str, Any], height: str = "560px") -> str:
    """Build a graph with circular nodes and labels inside, with a blue color palette."""
    nodes = graph_json.get("nodes", [])
    edges = graph_json.get("edges", [])
    
    # Assign blue shades based on node type
    blue_shades = ["#5C7CBB", "#8A9FCD", "#6C8AC4", "#7B95C8", "#9FB1D9", "#4F6EAB"]
    type_colors = {}
    
    vis_nodes = []
    for n in nodes:
        ntype = n.get("type", "Unknown")
        if ntype not in type_colors:
            type_colors[ntype] = blue_shades[len(type_colors) % len(blue_shades)]
        
        color = type_colors[ntype]
        raw_label = n.get("label", n["id"]).split("\n")[0]
        # Wrap long labels
        label = textwrap.fill(raw_label, width=15)
        
        vis_nodes.append({
            "id": n["id"],
            "label": label,
            "title": f"{raw_label} ({ntype})",
            "color": {"background": color, "border": color, "highlight": {"background": "#3f5696", "border": "#3f5696"}},
            "shape": "circle",
            "font": {"color": "#000000", "size": 11, "face": "Inter, sans-serif"},
            "borderWidth": 0,
        })
        
    vis_edges = []
    for idx, e in enumerate(edges):
        vis_edges.append({
            "id": f"e{idx}",
            "from": e["source"],
            "to": e["target"],
            "label": e["relation"],
            "title": e["relation"],
            "arrows": "to",
            "color": {"color": "#8ca0ce", "highlight": "#5b72b0"},
            "font": {"size": 9, "align": "middle", "color": "#333", "face": "Inter, sans-serif", "background": "rgba(255,255,255,0.85)", "strokeWidth": 0},
            "smooth": {"type": "cubicBezier", "roundness": 0.5}
        })

    safe_nodes = json.dumps(vis_nodes).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    safe_edges = json.dumps(vis_edges).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
        <style type="text/css">
            body {{ margin: 0; padding: 0; font-family: 'Inter', system-ui, sans-serif; }}
            #mynetwork {{
                width: 100%;
                height: {height};
                border: 1px solid #E2E8F0;
                border-radius: 0 0 6px 6px;
                background-color: #ffffff;
            }}
            #stats-bar {{
                padding: 10px 16px;
                background: #F1F5F9;
                border: 1px solid #E2E8F0;
                border-bottom: none;
                border-radius: 6px 6px 0 0;
                font-size: 13px;
                color: #475569;
                font-weight: 500;
                display: flex;
                justify-content: space-between;
            }}
        </style>
    </head>
    <body>
        <div id="stats-bar">
            <span>Interactive Graph View (Blue Circles)</span>
            <span>{len(vis_nodes)} nodes / {len(vis_edges)} relationships</span>
        </div>
        <div id="mynetwork"></div>
        <script type="text/javascript">
            var nodes = new vis.DataSet({safe_nodes});
            var edges = new vis.DataSet({safe_edges});
            
            var container = document.getElementById('mynetwork');
            var data = {{ nodes: nodes, edges: edges }};
            var options = {{
                layout: {{
                    hierarchical: {{
                        enabled: true,
                        direction: 'UD',
                        sortMethod: 'directed',
                        levelSeparation: 150,
                        nodeSpacing: 200,
                        treeSpacing: 200
                    }}
                }},
                physics: {{
                    enabled: true,
                    hierarchicalRepulsion: {{
                        centralGravity: 0.0,
                        springLength: 150,
                        springConstant: 0.01,
                        nodeDistance: 200,
                        damping: 0.09
                    }},
                    solver: 'hierarchicalRepulsion'
                }},
                interaction: {{
                    hover: true,
                    zoomView: true,
                    dragView: true
                }}
            }};
            var network = new vis.Network(container, data, options);
        </script>
    </body>
    </html>
    """
    return html


# ---------------------------------------------------------------------------
# Backend config helpers
# ---------------------------------------------------------------------------

def get_secret(key: str) -> str:
    """Read a secret from .streamlit/secrets.toml or OS environment variables."""
    try:
        # First try Streamlit secrets
        val = st.secrets.get(key, "")
        if val:
            return val
    except Exception:
        pass
        
    # Fallback to standard environment variables (used by Replit, Docker, etc)
    import os
    return os.getenv(key, "")
def get_llm_config() -> tuple[str, str, str, str]:
    """Read all LLM config from backend secrets.
    Returns (host, token, model, ncbi_key).
    """
    host = get_secret("DATABRICKS_HOST") or DEFAULT_DATABRICKS_HOST
    token = get_secret("DATABRICKS_TOKEN")
    model = get_secret("DATABRICKS_MODEL") or DEFAULT_DATABRICKS_MODEL
    ncbi_key = get_secret("NCBI_API_KEY")
    return host, token, model, ncbi_key


# ---------------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------------

def inject_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
        
        /* Typography */
        html, body, [class*="css"]  {
            font-family: 'Inter', system-ui, sans-serif !important;
        }
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Inter', system-ui, sans-serif !important;
            font-weight: 600 !important;
            color: #0F172A !important;
        }
        p, span, div {
            font-weight: 400;
        }
        
        /* Layout and spacing */
        .block-container {
            padding-top: 32px !important;
            padding-bottom: 32px !important;
            padding-left: 24px !important;
            padding-right: 24px !important;
            max-width: 1200px;
        }
        hr {
            margin-top: 16px;
            margin-bottom: 16px;
            border-color: #E2E8F0;
        }
        
        /* Components: Buttons */
        .stButton button {
            border-radius: 6px !important;
            border: 1px solid #CBD5E1 !important;
            box-shadow: none !important;
            font-weight: 500 !important;
            height: 36px !important;
            padding: 0 16px !important;
        }
        .stButton button:hover {
            border-color: #94A3B8 !important;
            background-color: #F8FAFC !important;
            color: #0F172A !important;
        }
        /* Primary button override */
        .stButton button[data-baseweb="button"]:has(div[data-testid="stMarkdownContainer"]:empty) {
            /* Streamlit specific hack for primary if needed, but primary is handled by theme config */
        }
        
        /* Inputs & text areas */
        .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
            border-radius: 6px !important;
            border: 1px solid #CBD5E1 !important;
            box-shadow: none !important;
            padding: 8px 12px !important;
        }
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            border-right: 1px solid #E2E8F0;
        }
        
        /* Expander */
        .streamlit-expanderHeader {
            border-radius: 6px !important;
            font-weight: 500 !important;
        }
        
        /* Dataframes */
        .stDataFrame {
            border: 1px solid #E2E8F0 !important;
            border-radius: 6px !important;
            overflow: hidden;
        }
        
        /* Remove extra paddings and declutter */
        div.stMarkdown {
            margin-bottom: 8px;
        }
        </style>
    """, unsafe_allow_html=True)
    
def generate_cypher_script(graph_json: dict[str, Any]) -> str:
    """Convert JSON graph representation to a Neo4j Cypher script."""
    if not graph_json:
        return ""
        
    lines = []
    lines.append("// Cypher script generated by AORTA")
    lines.append("// Uncomment the next line to clear the database before loading:")
    lines.append("// MATCH (n) DETACH DELETE n;")
    lines.append("")
    
    # Create nodes
    for n in graph_json.get("nodes", []):
        node_id = n["id"].replace("'", "\\'")
        label = n.get("label", n["id"]).replace("'", "\\'")
        ntype = n.get("type", "Entity").replace("'", "").replace(" ", "_")
        lines.append(f"MERGE (n:{ntype} {{uri: '{node_id}'}}) SET n.name = '{label}';")
        
    lines.append("")
    
    # Create edges
    for e in graph_json.get("edges", []):
        source = e["source"].replace("'", "\\'")
        target = e["target"].replace("'", "\\'")
        rel = e.get("label", "RELATED_TO").upper().replace(" ", "_").replace("-", "_")
        lines.append(f"MATCH (a {{uri: '{source}'}})")
        lines.append(f"MATCH (b {{uri: '{target}'}})")
        lines.append(f"MERGE (a)-[:{rel}]->(b);")
        
    return "\n".join(lines)
def main() -> None:
    st.set_page_config(
        page_title="AORTA",
        layout="wide",
    )
    

    inject_custom_css()

    st.title("AORTA")
    st.markdown("#### Assay Ontology & Retrieval Translation Architect")

    # ── Load BAO reference (cached) ──
    bao_labels = load_bao_labels()

    # ── Read LLM config from backend ──
    databricks_host, databricks_token, databricks_model, ncbi_key = get_llm_config()

    # ── Session defaults ──
    if "doc" not in st.session_state:
        st.session_state.doc = None
    if "entities" not in st.session_state:
        st.session_state.entities = []
    if "graph" not in st.session_state:
        st.session_state.graph = None
    if "graph_json" not in st.session_state:
        st.session_state.graph_json = None

    # ── Chatbot session state ──
    # POC SCOPE: The chatbot queries whatever graph is in st.session_state["graph"]
    # — the document(s) already ingested this session.  If multiple documents
    # have been ingested, the chatbot answers across all of them since they
    # share the same in-memory rdflib.Graph.  No cross-session persistence.
    # Revisit this assumption if cross-session storage becomes a requirement.
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "chat_tool_traces" not in st.session_state:
        st.session_state.chat_tool_traces = []
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = chat_storage.create_conversation("New Conversation")

    # ── Sidebar ──
    with st.sidebar:
        if os.path.exists("logo.png"):
            st.image("logo.png", use_container_width=True)
            
        st.header("Chat History")
        conversations = chat_storage.list_conversations()
        
        # New chat button
        if st.button("➕ New Chat", use_container_width=True):
            st.session_state.conversation_id = chat_storage.create_conversation("New Conversation")
            st.session_state.chat_messages = []
            st.session_state.chat_tool_traces = []
            st.session_state.doc = None
            st.session_state.entities = []
            st.session_state.graph_json = None
            st.session_state.graph = None
            vector_db.set_chunks([])
            st.rerun()
            
        # Select conversation
        if conversations:
            conv_options = {c["id"]: f"{c['title']} ({c['created_at'][:10]})" for c in conversations}
            selected_conv = st.selectbox(
                "Recent conversations",
                options=list(conv_options.keys()),
                format_func=lambda x: conv_options[x],
                index=list(conv_options.keys()).index(st.session_state.conversation_id) 
                      if st.session_state.conversation_id in conv_options else 0,
                label_visibility="collapsed"
            )
            
            if selected_conv != st.session_state.conversation_id:
                st.session_state.conversation_id = selected_conv
                # Load history for selected
                msgs = chat_storage.get_conversation_messages(selected_conv)
                st.session_state.chat_messages = [{"role": m["role"], "content": m["content"], "sources_enabled": m.get("sources_enabled", [])} for m in msgs]
                # Reconstruct trace parallel array
                st.session_state.chat_tool_traces = [m["tool_traces"] for m in msgs if m["role"] == "assistant"]
                
                # Load run state
                run_state = chat_storage.get_conversation_state(selected_conv)
                if run_state and run_state.get("doc"):
                    st.session_state.doc = run_state.get("doc")
                    st.session_state.entities = run_state.get("entities", [])
                    st.session_state.graph_json = run_state.get("graph_json")
                    
                    graph_xml = run_state.get("graph_xml")
                    if graph_xml:
                        g = Graph()
                        g.parse(data=graph_xml, format="xml")
                        st.session_state.graph = g
                    else:
                        st.session_state.graph = None
                        
                    vector_chunks = run_state.get("vector_chunks")
                    if vector_chunks:
                        vector_db.set_chunks(vector_chunks)
                    else:
                        vector_db.set_chunks([])
                else:
                    st.session_state.doc = None
                    st.session_state.entities = []
                    st.session_state.graph_json = None
                    st.session_state.graph = None
                    vector_db.set_chunks([])
                    
                st.rerun()

            with st.expander("Manage chat"):
                current_title = next((c["title"] for c in conversations if c["id"] == st.session_state.conversation_id), "New Conversation")
                new_title = st.text_input("New title", value=current_title, key="rename_chat_input", label_visibility="collapsed")
                if st.button("Save Name", use_container_width=True, key="rename_chat_btn"):
                    if new_title.strip() and new_title != current_title:
                        chat_storage.update_conversation_title(st.session_state.conversation_id, new_title.strip())
                        st.rerun()
                        
                st.markdown("---")
                if st.button("Delete Chat", type="primary", use_container_width=True, key="delete_chat_btn"):
                    chat_storage.delete_conversation(st.session_state.conversation_id)
                    st.session_state.conversation_id = str(uuid.uuid4())
                    st.session_state.chat_messages = []
                    st.session_state.chat_tool_traces = []
                    st.session_state.doc = None
                    st.session_state.entities = []
                    st.session_state.graph_json = None
                    st.session_state.graph = None
                    vector_db.set_chunks([])
                    st.rerun()
                        
        st.divider()
        st.header("Input")

        # Input mode
        input_mode = st.radio(
            "Input method",
            ["PMID / PubMed URL", "Upload document", "Paste text"],
            index=0,
        )

        pmid_input = ""
        pasted_text = ""
        pasted_title = "Pasted document"
        uploaded_file = None

        if input_mode == "PMID / PubMed URL":
            pmid_input = st.text_input(
                "PMID or PubMed URL",
                placeholder="e.g. 38123456 or https://pubmed.ncbi.nlm.nih.gov/38123456/",
            )

        elif input_mode == "Upload document":
            uploaded_file = st.file_uploader(
                "Upload a document",
                type=["txt", "md", "pdf", "docx", "csv", "xlsx", "json", "xml"],
                help="Supported: TXT, MD, PDF, DOCX, CSV, XLSX, JSON, XML (Max 200MB)",
            )

        else:  # Paste text
            pasted_title = st.text_input("Document title (optional)", value="Pasted document")
            pasted_text = st.text_area(
                "Paste abstract or text",
                height=200,
                placeholder="Paste text content...",
            )

        col1, col2 = st.columns(2)
        with col1:
            fetch_btn = st.button("Fetch", use_container_width=True)
        with col2:
            process_btn = st.button("Process", type="primary", use_container_width=True)

    # ── Fetch document ──
    if fetch_btn:
        st.session_state.graph = None
        st.session_state.graph_json = None
        st.session_state.entities = []

        if input_mode == "PMID / PubMed URL":
            pmid = parse_pmid(pmid_input)
            if not pmid:
                st.error("Invalid PMID or URL. Enter a numeric PMID or a PubMed link.")
            else:
                try:
                    doc = fetch_pubmed(pmid, api_key=ncbi_key or None)
                    st.session_state.doc = doc
                    st.success(f"Fetched PMID {pmid}.")
                except requests.RequestException as exc:
                    st.error(f"PubMed fetch failed: {exc}")
                    st.session_state.doc = None
                except ValueError as exc:
                    st.error(str(exc))
                    st.session_state.doc = None

        elif input_mode == "Upload document":
            if uploaded_file is None:
                st.error("Please upload a file first.")
            else:
                try:
                    text_content = extract_text_from_file(uploaded_file)
                    if not text_content.strip():
                        st.error("No text could be extracted from the uploaded file.")
                    else:
                        st.session_state.doc = {
                            "pmid": None,
                            "title": uploaded_file.name,
                            "abstract": text_content.strip(),
                        }
                        st.success(f"Loaded: {uploaded_file.name} ({len(text_content):,} characters)")
                except Exception as exc:
                    st.error(f"Failed to read file: {exc}")
                    st.session_state.doc = None

        else:  # Paste text
            if not pasted_text.strip():
                st.error("Paste some text before fetching.")
            else:
                st.session_state.doc = {
                    "pmid": None,
                    "title": pasted_title or "Pasted document",
                    "abstract": pasted_text.strip(),
                }
                st.success("Text loaded.")

    # ── Process ──
    if process_btn:
        # Always update doc from current inputs before processing
        if input_mode == "PMID / PubMed URL" and pmid_input.strip():
            pmid = parse_pmid(pmid_input)
            if pmid:
                try:
                    st.session_state.doc = fetch_pubmed(pmid, api_key=ncbi_key or None)
                except Exception as exc:
                    st.error(f"Could not fetch document: {exc}")
        elif input_mode == "Upload document" and uploaded_file is not None:
            try:
                text_content = extract_text_from_file(uploaded_file)
                st.session_state.doc = {
                    "pmid": None,
                    "title": uploaded_file.name,
                    "abstract": text_content.strip(),
                }
            except Exception as exc:
                st.error(f"Failed to read file: {exc}")
        elif input_mode == "Paste text" and pasted_text.strip():
            st.session_state.doc = {
                "pmid": None,
                "title": pasted_title or "Pasted document",
                "abstract": pasted_text.strip(),
            }

        doc = st.session_state.doc
        if not doc or not doc.get("abstract", "").strip():
            st.error("No document to process. Fetch a PMID, upload a file, or paste text first.")
        else:
            progress_bar = st.progress(5, text="Initializing extraction...")
            
            progress_bar.progress(15, text="Extracting entities via LLM (this may take a moment)...")
            extraction_data, err = extract_entities(
                doc["abstract"],
                databricks_host=databricks_host,
                databricks_token=databricks_token,
                databricks_model=databricks_model,
            )
            if err:
                st.error(err)

            # Surface post-extraction validation warning (zero results despite endpoints)
            if extraction_data.get("_validation_warning"):
                st.warning(extraction_data["_validation_warning"])

            progress_bar.progress(60, text="Normalizing and deduplicating entities...")
            # Deduplicate similar entities
            normalize_entities(extraction_data)

            entities = extraction_data.get("entities", [])
            if not entities and not err:
                st.warning("No entities extracted. The LLM did not find biomedical entities in this text. Graph will contain publication node only.")
            st.session_state.entities = entities

            progress_bar.progress(70, text="Generating cross-references...")
            # Add NCBI links to entity data for display
            for ent in st.session_state.entities:
                ent["ncbi_link"] = generate_db_link(
                    ent.get("identifier"), ent["normalized_name"], ent["category"]
                )

            progress_bar.progress(80, text="Building semantic Ontology Graph...")
            g = build_ontology(
                extraction_data=extraction_data,
                title=doc.get("title", ""),
                pmid=doc.get("pmid"),
                text=doc["abstract"],
                bao_labels=bao_labels,
            )
            violations = validate_graph(g)
            if violations:
                st.warning("Ontology Domain/Range Violations Detected:\n" + "\n".join(f"- {v}" for v in violations))
                
            st.session_state.graph = g
            st.session_state.graph_json = graph_to_json(g)
            
            progress_bar.progress(90, text="Indexing document into Vector Database...")
            # Add to vector DB
            if doc.get("abstract"):
                vector_db.add_document(
                    title=doc.get("title", ""),
                    pmid=doc.get("pmid", ""),
                    text=doc["abstract"]
                )
            
            progress_bar.progress(95, text="Saving session state...")
            # Save session run state
            if hasattr(st.session_state, "conversation_id"):
                owl_xml_str = g.serialize(format="xml")
                if isinstance(owl_xml_str, bytes):
                    owl_xml_str = owl_xml_str.decode("utf-8")
                chat_storage.update_conversation_run_data(
                    st.session_state.conversation_id,
                    doc=st.session_state.doc,
                    entities=st.session_state.entities,
                    graph_json=st.session_state.graph_json,
                    graph_xml=owl_xml_str,
                    vector_chunks=vector_db.chunks
                )
                
            progress_bar.progress(100, text="Processing complete!")
            time.sleep(0.5)
            progress_bar.empty()
            st.success("Document successfully processed and indexed.")

    # ── Main panel ──
    doc = st.session_state.doc
    if doc:
        st.subheader("Document")
        if doc.get("pmid"):
            st.markdown(
                f"**PMID:** [{doc['pmid']}](https://pubmed.ncbi.nlm.nih.gov/{doc['pmid']}/)"
            )
        st.markdown(f"**Title:** {doc.get('title', '(untitled)')}")
        st.markdown("**Text**")
        preview = doc.get("abstract", "")
        st.text_area(
            "Text preview",
            value=preview,
            height=180,
            disabled=True,
            label_visibility="collapsed",
        )
    else:
        st.info("Use the sidebar to fetch a PubMed article, upload a document, or paste text, then click **Process**.")

    # ── Extracted entities with NCBI links ──
    if st.session_state.entities:
        st.subheader("Extracted Entities")
        st.dataframe(
            st.session_state.entities,
            use_container_width=True,
            column_order=["text", "category", "normalized_name", "identifier", "ncbi_link"],
            column_config={
                "text": st.column_config.TextColumn("Text span"),
                "category": st.column_config.TextColumn("Category"),
                "normalized_name": st.column_config.TextColumn("Normalized name"),
                "identifier": st.column_config.TextColumn("CURIE"),
                "ncbi_link": st.column_config.LinkColumn(
                    "NCBI / DB Link",
                    display_text="Open",
                    help="Click to open NCBI or database page for this entity",
                ),
            },
        )
    elif st.session_state.graph is not None:
        st.subheader("Extracted Entities")
        st.caption("No entities were extracted.")

    # ── Graph and downloads ──
    if st.session_state.graph is not None and st.session_state.graph_json is not None:
        g: Graph = st.session_state.graph
        graph_json = st.session_state.graph_json

        col_hdr, col_btn = st.columns([1, 1])
        with col_hdr:
            st.subheader("Ontology Graph")
        with col_btn:
            view_style = st.selectbox(
                "Graph Style",
                options=["Standard", "Neo4j-style", "Blue Circles"],
                index=["Standard", "Neo4j-style", "Blue Circles"].index(st.session_state.get("graph_view_style", "Standard")) if "graph_view_style" in st.session_state else 0,
                key="graph_style_select",
                label_visibility="collapsed",
            )
            st.session_state["graph_view_style"] = view_style

        try:
            view_style = st.session_state.get("graph_view_style", "Standard")
            if view_style == "Neo4j-style":
                html = render_neo4j_html(graph_json)
                st.components.v1.html(html, height=620, scrolling=False)
                st.info("Note: This view is purely front-end and does not require a running Neo4j instance. Want to explore this in real Neo4j? Use the Cypher/CSV export below.")
            elif view_style == "Blue Circles":
                html = render_blue_circle_html(graph_json)
                st.components.v1.html(html, height=620, scrolling=False)
            else:
                html = render_pyvis_html(graph_json)
                st.components.v1.html(html, height=560, scrolling=True)
        except Exception as exc:
            st.warning(f"Graph visualization failed: {exc}")

        # ── Downloads ──
        st.subheader("Downloads")

        # Serialize OWL (RDF/XML) — WebProtégé compatible
        owl_xml_str = g.serialize(format="xml")
        if isinstance(owl_xml_str, bytes):
            owl_xml_str = owl_xml_str.decode("utf-8")
            
        # Also provide Turtle
        ttl_str = g.serialize(format="turtle")
        if isinstance(ttl_str, bytes):
            ttl_str = ttl_str.decode("utf-8")
            
        json_str = json.dumps(graph_json, indent=2)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.download_button(
                "OWL (RDF/XML)",
                data=owl_xml_str,
                file_name="ontology.owl",
                mime="application/rdf+xml",
                use_container_width=True,
                help="WebProtégé-compatible OWL format",
            )
        with col2:
            st.download_button(
                "Turtle (.ttl)",
                data=ttl_str,
                file_name="ontology.ttl",
                mime="text/turtle",
                use_container_width=True,
            )
        with col3:
            st.download_button(
                "JSON graph",
                data=json_str,
                file_name="ontology_graph.json",
                mime="application/json",
                use_container_width=True,
            )
        with col4:
            cypher_str = generate_cypher_script(graph_json)
            st.download_button(
                "Neo4j Cypher",
                data=cypher_str,
                file_name="ontology.cypher",
                mime="application/x-cypher-query",
                use_container_width=True,
                help="Cypher script for Neo4j import",
            )

        with st.expander("Raw OWL/XML preview"):
            st.code(g.serialize(format="xml"), language="xml")

        with st.expander("Raw Turtle preview"):
            st.code(g.serialize(format="turtle"), language="turtle")

        with st.expander("Raw JSON preview"):
            st.code(json.dumps(graph_json, indent=2), language="json")

    # ── Chatbot Panel: "Ask the Graph" ──
    if st.session_state.graph is not None:
        st.markdown("---")
        st.subheader("Hybrid GraphRAG Chatbot")
        
        # Source toggles
        col1, col2, col3 = st.columns(3)
        with col1:
            use_graph = st.checkbox("Graph", value=True, help="Use the ingested ontology graph.")
        with col2:
            use_vector = st.checkbox("Vector DB", value=True, help="Use the ingested document text chunks.")
        with col3:
            use_web = st.checkbox("Web Search", value=False, help="Search the live web for recent info.")
            
        enabled_sources = []
        enabled_tool_schemas = []
        if use_graph:
            enabled_sources.append("Graph")
            enabled_tool_schemas.extend([t for t in TOOL_SCHEMAS if t["function"]["name"] not in ("query_vector_db", "web_search")])
        if use_vector:
            enabled_sources.append("Vector DB")
            enabled_tool_schemas.extend([t for t in TOOL_SCHEMAS if t["function"]["name"] == "query_vector_db"])
        if use_web:
            enabled_sources.append("Web")
            enabled_tool_schemas.extend([t for t in TOOL_SCHEMAS if t["function"]["name"] == "web_search"])
            
        st.caption(
            "Ask natural-language questions using the enabled sources. "
            f"Currently enabled: {', '.join(enabled_sources) if enabled_sources else 'None'}"
        )

        # Display conversation history
        for idx, msg in enumerate(st.session_state.chat_messages):
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

                # Show tool-call provenance for assistant messages
                if msg["role"] == "assistant":
                    asst_idx = sum(
                        1 for m in st.session_state.chat_messages[:idx + 1]
                        if m["role"] == "assistant"
                    ) - 1
                    if asst_idx < len(st.session_state.chat_tool_traces):
                        trace = st.session_state.chat_tool_traces[asst_idx]
                        sources = msg.get("sources_enabled", [])
                        
                        # Display specific citations if vector DB was used
                        if trace:
                            vector_results = []
                            for step in trace:
                                if step['tool'] == 'query_vector_db' and isinstance(step.get('result'), list):
                                    vector_results.extend(step['result'])
                                    
                            if vector_results:
                                with st.expander("📚 Source Citations (Vector DB)", expanded=False):
                                    for res in vector_results:
                                        if isinstance(res, dict) and "text" in res:
                                            score = res.get("similarity_score", "N/A")
                                            st.markdown(f"**Document:** {res.get('source_doc', 'Unknown')} | **Chunk:** `{res.get('chunk_id')}` (Sim: {score})")
                                            st.info(res["text"])
                        
                        if trace:
                            with st.expander(
                                f"🔍 Tool calls used ({len(trace)} call{'s' if len(trace) != 1 else ''} | Sources: {','.join(sources) if sources else 'Unknown'})",
                                expanded=False,
                            ):
                                for step in trace:
                                    st.markdown(
                                        f"**Round {step['round']}** — "
                                        f"`{step['tool']}({json.dumps(step['arguments'], default=str)})`"
                                    )
                                    result_str = json.dumps(step["result"], indent=2, default=str)
                                    if len(result_str) > 3000:
                                        result_str = result_str[:3000] + "\n... (truncated)"
                                    st.code(result_str, language="json")

        # Chat input
        if not enabled_sources:
            st.warning("Please enable at least one source to ask a question.")
            st.chat_input("Select a source above...", disabled=True)
        elif user_input := st.chat_input("Ask a question…", key="chatbot_input"):
            # Persist and append user message
            chat_storage.add_message(
                st.session_state.conversation_id, "user", user_input, None, enabled_sources
            )
            st.session_state.chat_messages.append(
                {"role": "user", "content": user_input, "sources_enabled": enabled_sources}
            )

            llm_history = []
            recent = st.session_state.chat_messages[-20:]
            for m in recent[:-1]:
                llm_history.append({"role": m["role"], "content": m["content"]})

            answer = "(No response)"
            trace = []
            
            with st.status(f"Querying ({', '.join(enabled_sources)})...", expanded=True) as status:
                progress_bar = st.progress(0.0)
                
                for step_type, label, detail, progress_frac, current_trace in run_chatbot_loop_stream(
                    host=databricks_host,
                    token=databricks_token,
                    model=databricks_model,
                    graph=st.session_state.graph,
                    user_message=user_input,
                    history=llm_history,
                    enabled_tool_schemas=enabled_tool_schemas
                ):
                    status.update(label=label)
                    progress_bar.progress(progress_frac)
                    
                    if step_type == STEP_ERROR:
                        st.error(detail)
                    elif step_type == STEP_TOOL_DONE:
                        st.success(detail)
                    elif step_type in (STEP_TOOL_REQ, STEP_TOOL_EXEC):
                        st.info(detail)
                    elif step_type != STEP_DONE:
                        st.caption(detail)
                        
                    if step_type == STEP_DONE:
                        answer = detail
                        trace = current_trace
                        if "error" in label.lower():
                            status.update(label="Query failed", state="error", expanded=True)
                        else:
                            status.update(label="Query complete", state="complete", expanded=False)
                        progress_bar.progress(1.0)
                        break
                        
            # Persist and append assistant response
            chat_storage.add_message(
                st.session_state.conversation_id, "assistant", answer, trace, enabled_sources
            )
            st.session_state.chat_messages.append(
                {"role": "assistant", "content": answer, "sources_enabled": enabled_sources}
            )
            st.session_state.chat_tool_traces.append(trace)

            st.rerun()


if __name__ == "__main__":
    main()
