import json
try:
    import tomllib as toml
except ImportError:
    import toml
from rdflib import Graph
from chatbot_llm import run_chatbot_loop
from chatbot_tools import TOOL_SCHEMAS
from vector_db import vector_db

def run_tests():
    with open(".streamlit/secrets.toml", "rb") as f:
        secrets = toml.load(f)
    host = secrets["DATABRICKS_HOST"]
    token = secrets["DATABRICKS_TOKEN"]
    model = secrets.get("DATABRICKS_MODEL", "system.ai.gpt-5-5-pro")

    g = Graph()
    g.parse("test_graph.ttl", format="turtle")

    # Add a dummy vector DB document
    vector_db.add_document("Test Patent", "12345", "The patent states that Semaglutide is currently in Phase 1 trials and its formulation uses an advanced lipid nanoparticle delivery method to improve bioavailability by 45%. The statistical methodology involved a double-blind ANOVA.")

    test_cases = [
        {
            "name": "Graph-only (Graph enabled)",
            "query": "What targets does Semaglutide act on?",
            "enabled_tools": [t for t in TOOL_SCHEMAS if t["function"]["name"] not in ("query_vector_db", "web_search")],
            "expect_tools": ["find_entity", "get_relationships"]
        },
        {
            "name": "Vector-DB-appropriate (All enabled)",
            "query": "What does this patent say about the compound's formulation or delivery method?",
            "enabled_tools": TOOL_SCHEMAS,
            "expect_tools": ["query_vector_db"]
        },
        {
            "name": "Web-appropriate (All enabled)",
            "query": "What are the most recent news or clinical trial updates on Semaglutide from Eli Lilly in 2026?",
            "enabled_tools": TOOL_SCHEMAS,
            "expect_tools": ["web_search"]
        },
        {
            "name": "Conflict case (All enabled)",
            "query": "The document says Semaglutide is in Phase 1. Is that still true according to the web today?",
            "enabled_tools": TOOL_SCHEMAS,
            "expect_tools": ["query_vector_db", "web_search"]
        },
        {
            "name": "Adversarial (All enabled)",
            "query": "What's the current stock price impact of this patent?",
            "enabled_tools": TOOL_SCHEMAS,
            "expect_tools": [] # Should decline gracefully
        },
        {
            "name": "Graph-only enabled, ask for Web",
            "query": "What are the latest 2026 news updates on Semaglutide?",
            "enabled_tools": [t for t in TOOL_SCHEMAS if t["function"]["name"] not in ("query_vector_db", "web_search")],
            "expect_tools": [] # Should explicitly say it needs web
        }
    ]

    for tc in test_cases:
        print(f"\n{'='*60}\nTEST: {tc['name']}\nQUERY: {tc['query']}")
        
        answer, trace = run_chatbot_loop(
            host=host, token=token, model=model, graph=g, user_message=tc["query"], 
            enabled_tool_schemas=tc["enabled_tools"]
        )
        
        tools_used = [step["tool"] for step in trace]
        print(f"TOOLS USED: {tools_used}")
        print(f"ANSWER:\n{answer}\n")
        
        # Pass/fail
        passed = True
        for ext in tc["expect_tools"]:
            if ext not in tools_used:
                passed = False
                print(f"FAIL: Expected tool '{ext}' not used.")
        if tc["name"] == "Graph-only enabled, ask for Web" and "web" not in answer.lower():
             passed = False
             print(f"FAIL: Expected response to mention 'Web' search being disabled.")
        if passed:
             print("RESULT: PASS")

if __name__ == "__main__":
    run_tests()
