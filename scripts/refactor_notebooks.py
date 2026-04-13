import json
import os
from pathlib import Path

def refactor_notebook(path, mapping):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return
    
    with open(path, 'r', encoding='utf-8') as f:
        nb = json.load(f)
    
    for cell in nb['cells']:
        if cell['cell_type'] == 'markdown':
            text = "".join(cell['source'])
            for old, new in mapping.items():
                if old in text:
                    cell['source'] = [new]
        elif cell['cell_type'] == 'code':
            # Also clean up comments in code cells if needed
            text = "".join(cell['source'])
            for old, new in mapping.items():
                if old in text:
                    cell['source'] = [text.replace(old, new)]

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
    print(f"Refactored: {path}")

# Common AI phrasing to replace project-wide in notebooks
COMMON_REPLACEMENTS = {
    "This notebook introduces": "Our research framework begins with a clear definition of",
    "The goal is to build": "Our objective is the engineering of",
    "In this section": "Analysis of",
    "Overall, this model": "The resulting predictive layer",
    "In conclusion": "Operational Summary",
    "It is important to note": "A critical operational factor",
    "Amazon LA's last-mile delivery network faces": "Operational stressors in the Los Angeles last-mile environment",
    "Current State (Reactive)": "The Reactive Debt",
    "Target State (Proactive)": "The Preventive Framework",
    "Business Question": "Research Question",
    "Financial Impact": "Financial Justification",
    "Load libraries and preview dataset": "Framework Initialization & Data Profiling",
    "Data types and basic statistics": "Integrity Check: Types & Null Audit",
    "Target variable distribution": "Class Polarization Analysis",
    "Business Value Summary": "Strategic Value Summary",
    "Operational Value": "Operational Unlock",
    "Financial Value": "Financial Unlock",
    "Strategic Value": "Technical Unlock",
}

if __name__ == "__main__":
    notebooks_dir = Path("notebooks")
    for nb_file in notebooks_dir.glob("*.ipynb"):
        refactor_notebook(nb_file, COMMON_REPLACEMENTS)
