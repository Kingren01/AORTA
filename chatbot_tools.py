"""
Chatbot Tool Functions — Graph Query Layer
===========================================

Six deterministic Python functions that operate directly on the in-memory
rdflib Graph object built by the extraction pipeline.  Each returns a
JSON-serializable result (list of dicts or dict) for easy consumption by
the LLM and for unit-testing independently of the chatbot.

SCOPE ASSUMPTION (POC):
    These tools query whatever Graph is currently in st.session_state["graph"]
    — the document(s) already ingested this session.  If multiple documents
    have been ingested into the same session graph, the tools naturally query
    across all of them.  No cross-session persistence layer; revisit this
    assumption if persistent cross-document storage becomes a requirement.

NO new storage layer, NO SPARQL string-building by the LLM, NO vector store.
"""

from __future__ import annotations

import json
import re
from typing import Any

from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef
from rdflib.namespace import OWL, XSD

# ---------------------------------------------------------------------------
# Namespace mirrors — must match app.py constants exactly
# ---------------------------------------------------------------------------

ONTOLOGY_IRI = "http://ai-ontology.com/assay-ontology"
BASE_URI = ONTOLOGY_IRI + "/"
NS = Namespace(BASE_URI)
BAO = Namespace("http://www.bioassayontology.org/bao#")
OBO_NS = Namespace("http://www.geneontology.org/formats/oboInOwl#")

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
CLASS_URI_TO_NAME: dict[str, str] = {str(v): k for k, v in CLASS_URIS.items()}

# Data-property URIs (mirrors app.py)
DP_NORMALIZED_NAME = NS.normalizedName
DP_MENTIONED_IN = NS.mentionedInText
DP_DB_XREF = OBO_NS.hasDbXref
DP_HAS_VALUE = NS.hasValue
DP_HAS_UNIT = NS.hasUnit
DP_HAS_METRIC_TYPE = NS.hasMetricType
DP_HAS_MODALITY = NS.hasModality
DP_HAS_DEVELOPMENT_STAGE = NS.hasDevelopmentStage
DP_HAS_DEVELOPMENT_CODE = NS.hasDevelopmentCode
DP_HAS_ASSAY_DESIGN = NS.hasAssayDesign
DP_HAS_DETECTION_TECHNOLOGY = NS.hasDetectionTechnology
DP_HAS_PROVENANCE = NS.hasProvenance
DP_HAS_PATENT_NUMBER = NS.hasPatentNumber
DP_HAS_EXPIRATION_DATE = NS.hasExpirationDate
DP_TITLE = NS.title
DP_PMID = NS.pmid

# BAO metric-type URIs used in the graph
BAO_EC50 = BAO["BAO_0000188"]
BAO_IC50 = BAO["BAO_0000190"]

# Predicates that are schema-level / should be excluded from relationship results
_SCHEMA_PREDICATES = {
    str(RDF.type), str(RDFS.label), str(RDFS.subClassOf),
    str(RDFS.domain), str(RDFS.range),
    str(OWL.imports), str(OWL.versionInfo), str(OWL.unionOf),
}

# Data-property URIs to exclude from relationship traversal
_DATA_PROPERTIES = {
    str(DP_NORMALIZED_NAME), str(DP_MENTIONED_IN), str(DP_DB_XREF),
    str(DP_HAS_VALUE), str(DP_HAS_UNIT), str(DP_HAS_METRIC_TYPE),
    str(DP_HAS_MODALITY), str(DP_HAS_DEVELOPMENT_STAGE),
    str(DP_HAS_DEVELOPMENT_CODE), str(DP_HAS_ASSAY_DESIGN),
    str(DP_HAS_DETECTION_TECHNOLOGY), str(DP_HAS_PROVENANCE),
    str(DP_HAS_PATENT_NUMBER), str(DP_HAS_EXPIRATION_DATE),
    str(DP_TITLE), str(DP_PMID), str(NS.extractionMethod),
}

MAX_RESULTS = 20  # cap per tool call to keep LLM context manageable


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _uri_local_name(uri: URIRef | str) -> str:
    """Extract the local (fragment / last-segment) name from a URI."""
    s = str(uri)
    if "#" in s:
        return s.rsplit("#", 1)[-1]
    return s.rsplit("/", 1)[-1]


def _get_entity_class(g: Graph, uri: URIRef) -> str | None:
    """Return the ontology class name for an individual, or None."""
    for _, _, o in g.triples((uri, RDF.type, None)):
        cls_name = CLASS_URI_TO_NAME.get(str(o))
        if cls_name:
            return cls_name
    return None


def _get_entity_name(g: Graph, uri: URIRef) -> str:
    """Return the normalizedName (preferred) or rdfs:label for an entity."""
    for _, _, lit in g.triples((uri, DP_NORMALIZED_NAME, None)):
        return str(lit)
    for _, _, lit in g.triples((uri, RDFS.label, None)):
        return str(lit)
    return _uri_local_name(uri)


def _get_all_literals(g: Graph, uri: URIRef, pred: URIRef) -> list[str]:
    """Collect all literal values for (uri, pred, ?)."""
    return [str(o) for _, _, o in g.triples((uri, pred, None)) if isinstance(o, Literal)]


def _is_object_property_edge(g: Graph, pred: URIRef) -> bool:
    """Return True if the predicate is an object property (not schema/data)."""
    ps = str(pred)
    if ps in _SCHEMA_PREDICATES or ps in _DATA_PROPERTIES:
        return False
    return True


def _resolve_metric_type(g: Graph, metric_term) -> str:
    """Convert a metric type (BAO URI or Literal) to a readable string."""
    if metric_term == BAO_EC50:
        return "EC50"
    if metric_term == BAO_IC50:
        return "IC50"
    if isinstance(metric_term, URIRef):
        return _uri_local_name(metric_term)
    return str(metric_term)


def _fuzzy_match(query: str, text: str) -> bool:
    """Case-insensitive substring match with basic normalization."""
    q = re.sub(r"[\s_\-]+", "", query.lower())
    t = re.sub(r"[\s_\-]+", "", text.lower())
    return q in t or t in q


def _get_all_individuals(g: Graph) -> list[tuple[URIRef, str]]:
    """Return all (uri, class_name) pairs for named individuals."""
    results = []
    for uri, _, cls_uri in g.triples((None, RDF.type, None)):
        if not isinstance(uri, URIRef):
            continue
        cls_name = CLASS_URI_TO_NAME.get(str(cls_uri))
        if cls_name:
            results.append((uri, cls_name))
    return results


# ---------------------------------------------------------------------------
# TOOL 1: find_entity
# ---------------------------------------------------------------------------

def find_entity(g: Graph, name: str) -> list[dict[str, Any]]:
    """
    Fuzzy-match ``name`` against normalizedName and mentionedInText across
    all entity classes.  Returns candidate matches with URI, class, name,
    and cross-references for disambiguation.

    Parameters
    ----------
    g : rdflib.Graph
        The session ontology graph.
    name : str
        The search term (e.g. "semaglutide", "GLP1", "Eli Lilly").

    Returns
    -------
    list[dict]
        Each dict: {uri, entity_class, normalizedName, dbXrefs, mentionedInText}
    """
    if not name or not name.strip():
        return []

    query = name.strip()
    matches: dict[str, dict] = {}  # keyed by URI string to deduplicate

    for uri, cls_name in _get_all_individuals(g):
        uri_str = str(uri)
        if uri_str in matches:
            continue

        # Check normalizedName
        norm_names = _get_all_literals(g, uri, DP_NORMALIZED_NAME)
        # Check mentionedInText
        mentions = _get_all_literals(g, uri, DP_MENTIONED_IN)
        # Check rdfs:label
        labels = _get_all_literals(g, uri, RDFS.label)

        all_texts = norm_names + mentions + labels
        if any(_fuzzy_match(query, t) for t in all_texts):
            db_xrefs = _get_all_literals(g, uri, DP_DB_XREF)
            matches[uri_str] = {
                "uri": uri_str,
                "entity_class": cls_name,
                "normalizedName": norm_names[0] if norm_names else _uri_local_name(uri),
                "dbXrefs": db_xrefs,
                "mentionedInText": mentions[:5],  # cap to avoid huge payloads
            }

    results = list(matches.values())[:MAX_RESULTS]
    return results


# ---------------------------------------------------------------------------
# TOOL 2: get_entity_details
# ---------------------------------------------------------------------------

def get_entity_details(g: Graph, uri: str) -> dict[str, Any]:
    """
    Return all data properties and a summary of outgoing/incoming object
    properties for a single entity.

    Parameters
    ----------
    g : rdflib.Graph
    uri : str
        The full URI string of the entity.

    Returns
    -------
    dict
        Full entity record with data properties and relationship summaries.
    """
    entity_uri = URIRef(uri)
    cls_name = _get_entity_class(g, entity_uri)

    if cls_name is None:
        return {"error": f"No entity found with URI: {uri}"}

    record: dict[str, Any] = {
        "uri": uri,
        "entity_class": cls_name,
        "normalizedName": _get_entity_name(g, entity_uri),
    }

    # Collect all data properties
    dp_map = {
        DP_DB_XREF: "dbXrefs",
        DP_MENTIONED_IN: "mentionedInText",
        DP_HAS_MODALITY: "hasModality",
        DP_HAS_DEVELOPMENT_STAGE: "hasDevelopmentStage",
        DP_HAS_DEVELOPMENT_CODE: "hasDevelopmentCode",
        DP_HAS_ASSAY_DESIGN: "hasAssayDesign",
        DP_HAS_DETECTION_TECHNOLOGY: "hasDetectionTechnology",
        DP_HAS_VALUE: "hasValue",
        DP_HAS_UNIT: "hasUnit",
        DP_HAS_METRIC_TYPE: "hasMetricType",
        DP_HAS_PROVENANCE: "hasProvenance",
        DP_HAS_PATENT_NUMBER: "hasPatentNumber",
        DP_HAS_EXPIRATION_DATE: "hasExpirationDate",
        DP_TITLE: "title",
        DP_PMID: "pmid",
    }

    for dp_uri, key in dp_map.items():
        vals = _get_all_literals(g, entity_uri, dp_uri)
        if vals:
            record[key] = vals if len(vals) > 1 else vals[0]

    # Resolve metric type from BAO URIs
    if "hasMetricType" in record:
        raw = record["hasMetricType"]
        if isinstance(raw, list):
            record["hasMetricType"] = [_resolve_metric_type(g, v) for v in raw]
        else:
            # Check if it's stored as a URI in the graph
            for _, _, mt in g.triples((entity_uri, DP_HAS_METRIC_TYPE, None)):
                record["hasMetricType"] = _resolve_metric_type(g, mt)
                break

    # Outgoing object properties
    outgoing: list[dict] = []
    for _, pred, obj in g.triples((entity_uri, None, None)):
        if not isinstance(obj, URIRef) or not _is_object_property_edge(g, pred):
            continue
        obj_cls = _get_entity_class(g, obj)
        if obj_cls:
            outgoing.append({
                "predicate": _uri_local_name(pred),
                "target_uri": str(obj),
                "target_class": obj_cls,
                "target_name": _get_entity_name(g, obj),
            })
    if outgoing:
        record["outgoing_relationships"] = outgoing

    # Incoming object properties
    incoming: list[dict] = []
    for subj, pred, _ in g.triples((None, None, entity_uri)):
        if not isinstance(subj, URIRef) or not _is_object_property_edge(g, pred):
            continue
        subj_cls = _get_entity_class(g, subj)
        if subj_cls:
            incoming.append({
                "predicate": _uri_local_name(pred),
                "source_uri": str(subj),
                "source_class": subj_cls,
                "source_name": _get_entity_name(g, subj),
            })
    if incoming:
        record["incoming_relationships"] = incoming

    return record


# ---------------------------------------------------------------------------
# TOOL 3: get_relationships
# ---------------------------------------------------------------------------

def get_relationships(g: Graph, uri: str, relation_type: str | None = None) -> list[dict[str, Any]]:
    """
    Return one-hop relationships from/to the given entity, optionally
    filtered to a specific predicate.

    Parameters
    ----------
    g : rdflib.Graph
    uri : str
        The full URI of the entity.
    relation_type : str, optional
        If provided, filter to edges matching this predicate name
        (e.g. "developedBy", "testsTarget").  Case-insensitive.

    Returns
    -------
    list[dict]
        Each: {direction, predicate, entity_uri, entity_class, entity_name}
    """
    entity_uri = URIRef(uri)
    results: list[dict] = []

    rel_filter = relation_type.strip().lower() if relation_type else None

    # Outgoing: (entity, pred, target)
    for _, pred, obj in g.triples((entity_uri, None, None)):
        if not isinstance(obj, URIRef) or not _is_object_property_edge(g, pred):
            continue
        pred_name = _uri_local_name(pred)
        if rel_filter and pred_name.lower() != rel_filter:
            continue
        obj_cls = _get_entity_class(g, obj)
        if obj_cls:
            results.append({
                "direction": "outgoing",
                "predicate": pred_name,
                "entity_uri": str(obj),
                "entity_class": obj_cls,
                "entity_name": _get_entity_name(g, obj),
            })

    # Incoming: (source, pred, entity)
    for subj, pred, _ in g.triples((None, None, entity_uri)):
        if not isinstance(subj, URIRef) or not _is_object_property_edge(g, pred):
            continue
        pred_name = _uri_local_name(pred)
        if rel_filter and pred_name.lower() != rel_filter:
            continue
        subj_cls = _get_entity_class(g, subj)
        if subj_cls:
            results.append({
                "direction": "incoming",
                "predicate": pred_name,
                "entity_uri": str(subj),
                "entity_class": subj_cls,
                "entity_name": _get_entity_name(g, subj),
            })

    return results[:MAX_RESULTS]


# ---------------------------------------------------------------------------
# TOOL 4: get_results
# ---------------------------------------------------------------------------

def get_results(
    g: Graph,
    compound: str | None = None,
    target: str | None = None,
    metric_type: str | None = None,
    max_value: float | None = None,
    min_value: float | None = None,
) -> list[dict[str, Any]]:
    """
    Query Result individuals with optional filtering by compound, target,
    metric type, and numeric value range.

    Parameters
    ----------
    g : rdflib.Graph
    compound : str, optional
        Compound name to filter by (fuzzy match).
    target : str, optional
        Target name to filter by (fuzzy match).
    metric_type : str, optional
        Metric type to filter by (e.g. "Ki", "IC50", "EC50").
    max_value : float, optional
        Maximum value filter (inclusive).
    min_value : float, optional
        Minimum value filter (inclusive).

    Returns
    -------
    list[dict]
        Each: {result_uri, compound_name, target_name, metric_type, value,
               unit, source_assay, source_document}
    """
    results: list[dict] = []

    # Find all Result individuals
    for res_uri, _, _ in g.triples((None, RDF.type, CLASS_URIS["Result"])):
        if not isinstance(res_uri, URIRef):
            continue

        # -- Extract result data --
        value_raw = None
        for _, _, v in g.triples((res_uri, DP_HAS_VALUE, None)):
            try:
                value_raw = float(str(v))
            except (ValueError, TypeError):
                value_raw = str(v)
            break

        unit = ""
        for _, _, u in g.triples((res_uri, DP_HAS_UNIT, None)):
            unit = str(u)
            break

        mt_str = ""
        for _, _, mt in g.triples((res_uri, DP_HAS_METRIC_TYPE, None)):
            mt_str = _resolve_metric_type(g, mt)
            break

        # -- Linked compound --
        cmpd_name = ""
        cmpd_uri = None
        for _, _, c in g.triples((res_uri, NS.forCompound, None)):
            if isinstance(c, URIRef):
                cmpd_uri = c
                cmpd_name = _get_entity_name(g, c)
            break

        # -- Linked target --
        tgt_name = ""
        tgt_uri = None
        for _, _, t in g.triples((res_uri, NS.forTarget, None)):
            if isinstance(t, URIRef):
                tgt_uri = t
                tgt_name = _get_entity_name(g, t)
            break

        # -- Apply filters --
        if compound and cmpd_name and not _fuzzy_match(compound, cmpd_name):
            continue
        if compound and not cmpd_name:
            continue

        if target and tgt_name and not _fuzzy_match(target, tgt_name):
            continue
        if target and not tgt_name:
            continue

        if metric_type and mt_str and not _fuzzy_match(metric_type, mt_str):
            continue
        if metric_type and not mt_str:
            continue

        if max_value is not None and isinstance(value_raw, (int, float)):
            if value_raw > max_value:
                continue

        if min_value is not None and isinstance(value_raw, (int, float)):
            if value_raw < min_value:
                continue

        # -- Find source assay (who has hasResult -> this result) --
        source_assay = ""
        for assay_uri, _, _ in g.triples((None, NS.hasResult, res_uri)):
            if isinstance(assay_uri, URIRef):
                source_assay = _get_entity_name(g, assay_uri)
            break

        # -- Find source document (Publication that mentionedInDocument) --
        source_doc = ""
        # Trace: assay or compound -> mentionedInDocument back-link from Publication
        for pub_uri, _, _ in g.triples((None, RDF.type, CLASS_URIS["Publication"])):
            if isinstance(pub_uri, URIRef):
                title_vals = _get_all_literals(g, pub_uri, DP_TITLE)
                pmid_vals = _get_all_literals(g, pub_uri, DP_PMID)
                if title_vals:
                    source_doc = title_vals[0]
                    if pmid_vals:
                        source_doc += f" (PMID: {pmid_vals[0]})"
                elif pmid_vals:
                    source_doc = f"PMID: {pmid_vals[0]}"
                break  # Use first publication found

        results.append({
            "result_uri": str(res_uri),
            "compound_name": cmpd_name,
            "compound_uri": str(cmpd_uri) if cmpd_uri else None,
            "target_name": tgt_name,
            "target_uri": str(tgt_uri) if tgt_uri else None,
            "metric_type": mt_str,
            "value": value_raw,
            "unit": unit,
            "source_assay": source_assay,
            "source_document": source_doc,
        })

    return results[:MAX_RESULTS]


# ---------------------------------------------------------------------------
# TOOL 5: compare_entities
# ---------------------------------------------------------------------------

def compare_entities(g: Graph, uri_a: str, uri_b: str) -> dict[str, Any]:
    """
    Return side-by-side details, relationships, and results for two entities.

    Parameters
    ----------
    g : rdflib.Graph
    uri_a : str
        Full URI of the first entity.
    uri_b : str
        Full URI of the second entity.

    Returns
    -------
    dict
        {entity_a: {details, relationships, results},
         entity_b: {details, relationships, results}}
    """
    def _entity_bundle(uri_str: str) -> dict:
        details = get_entity_details(g, uri_str)
        relationships = get_relationships(g, uri_str)
        # Query results linked to this entity (as compound or target)
        name = details.get("normalizedName", "")
        cls = details.get("entity_class", "")
        entity_results = []
        if cls == "Compound":
            entity_results = get_results(g, compound=name)
        elif cls == "Target":
            entity_results = get_results(g, target=name)
        return {
            "details": details,
            "relationships": relationships,
            "results": entity_results,
        }

    return {
        "entity_a": _entity_bundle(uri_a),
        "entity_b": _entity_bundle(uri_b),
    }


# ---------------------------------------------------------------------------
# TOOL_SCHEMAS — OpenAI-format function-calling JSON schemas
# ---------------------------------------------------------------------------

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "find_entity",
            "description": (
                "Search for entities in the ontology graph by name. Performs "
                "fuzzy matching against normalizedName and mentionedInText "
                "across all entity types (Target, Compound, Pathway, Assay, "
                "Measurement, AnalyticalMethod, Organization, Result). "
                "Use this FIRST to find entity URIs before calling other tools. "
                "Returns a list of candidate matches with URI, class, name, "
                "and cross-references."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": (
                            "The entity name to search for "
                            "(e.g. 'semaglutide', 'GLP-1 receptor', 'Eli Lilly')"
                        ),
                    }
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_entity_details",
            "description": (
                "Get the full details of a specific entity by its URI. "
                "Returns all data properties (normalizedName, dbXrefs, "
                "mentionedInText, modality, development stage/code, etc.) "
                "and summaries of outgoing and incoming object-property "
                "relationships. You must have the entity URI first — use "
                "find_entity to discover it."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "uri": {
                        "type": "string",
                        "description": (
                            "The full URI of the entity "
                            "(e.g. 'http://ai-ontology.com/assay-ontology/Compound_Semaglutide')"
                        ),
                    }
                },
                "required": ["uri"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_relationships",
            "description": (
                "Get one-hop relationships from/to a specific entity. "
                "Returns both outgoing and incoming edges with the connected "
                "entity's name, class, and URI. Optionally filter to a "
                "specific predicate (e.g. 'developedBy', 'testsTarget', "
                "'actsAsAgonistFor'). You must have the entity URI first."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "uri": {
                        "type": "string",
                        "description": "The full URI of the entity.",
                    },
                    "relation_type": {
                        "type": "string",
                        "description": (
                            "Optional: filter to a specific relationship predicate "
                            "(e.g. 'developedBy', 'testsTarget', 'actsAsAgonistFor', "
                            "'bindsToProtein', 'inhibits', 'sponsoredBy', 'hasResult'). "
                            "Omit to return all relationships."
                        ),
                    },
                },
                "required": ["uri"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_results",
            "description": (
                "Query experimental results (Result individuals) in the graph. "
                "Filter by compound name, target name, metric type "
                "(e.g. 'Ki', 'IC50', 'EC50'), and/or numeric value range. "
                "Returns compound name, target name, metric type, value, "
                "unit, source assay, and source document for provenance. "
                "Use this for questions about potency, affinity, or specific "
                "measured values."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "compound": {
                        "type": "string",
                        "description": "Optional: compound name to filter by (fuzzy match).",
                    },
                    "target": {
                        "type": "string",
                        "description": "Optional: target name to filter by (fuzzy match).",
                    },
                    "metric_type": {
                        "type": "string",
                        "description": (
                            "Optional: metric type to filter by "
                            "(e.g. 'Ki', 'IC50', 'EC50', 'Kd', 'Emax')."
                        ),
                    },
                    "max_value": {
                        "type": "number",
                        "description": "Optional: maximum value (inclusive) for numeric filtering.",
                    },
                    "min_value": {
                        "type": "number",
                        "description": "Optional: minimum value (inclusive) for numeric filtering.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_entities",
            "description": (
                "Compare two entities side by side. Returns full details, "
                "relationships, and associated experimental results for both "
                "entities. Use this when asked to compare compounds, targets, "
                "or any two entities. You need both entity URIs first — use "
                "find_entity to discover them."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "uri_a": {
                        "type": "string",
                        "description": "Full URI of the first entity.",
                    },
                    "uri_b": {
                        "type": "string",
                        "description": "Full URI of the second entity.",
                    },
                },
                "required": ["uri_a", "uri_b"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_vector_db",
            "description": (
                "Search the full text of the ingested documents for specific nuances, "
                "methodology, or qualitative descriptions not captured as formal ontology "
                "entities/relationships. Use this for questions like 'what does the text say about...' "
                "or 'how does the paper describe...'. Do NOT use this for finding targets or compounds."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Semantic search query.",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of chunks to return (default 15).",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Search the live web for current information, recent news, or external data "
                "not found in the documents or graph. Use this for questions asking about "
                "recent trials, competitor news, or whether something has changed recently."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query for DuckDuckGo.",
                    }
                },
                "required": ["query"],
            },
        },
    }
]
