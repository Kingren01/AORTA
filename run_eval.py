import sys
import json
try:
    import tomllib as toml
except ImportError:
    import toml
from app import extract_text_from_file, extract_entities

def run():
    with open(".streamlit/secrets.toml", "rb") as f:
        secrets = toml.load(f)
    host = secrets["DATABRICKS_HOST"]
    token = secrets["DATABRICKS_TOKEN"]
    # The prompt actually uses gpt-5-5-pro by default in app.py if not specified, 
    # but the secret has gpt-5-5. Let's use gpt-5-5-pro as in app.py's DEFAULT_DATABRICKS_MODEL.
    model = "system.ai.gpt-5-5-pro"

    class MockFile:
        def __init__(self, path):
            self.path = path
            self.file = open(path, "rb")
            self.name = path
        def read(self):
            return self.file.read()
        def seek(self, offset):
            self.file.seek(offset)
            
    pdf_file = MockFile(r"C:\Users\renis\Downloads\US9884093.pdf")
    text = extract_text_from_file(pdf_file)[:15000]
    print("Text extracted, length:", len(text))
    
    # Run extraction
    result, err = extract_entities(text, host, token, model)
    if err:
        print("Error:", err)
    
    with open("eval_results.json", "w") as f:
        json.dump(result, f, indent=2)
    print("Done writing eval_results.json")

if __name__ == "__main__":
    run()
