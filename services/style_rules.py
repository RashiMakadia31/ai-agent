import re
from typing import Dict, Any


def check_snake_case(name: str) -> bool:
    return re.fullmatch(r"[a-z_][a-z0-9_]*", name) is not None


def check_pascal_case(name: str) -> bool:
    return re.fullmatch(r"[A-Z][a-zA-Z0-9]*", name) is not None


def get_indent_style(code: str) -> Dict[str, Any]:
    lines = code.splitlines()
    spaces = [len(line) - len(line.lstrip(' ')) for line in lines if line.lstrip()]
    uses_tabs = any('\t' in line for line in lines)
    size = min((s for s in spaces if s > 0), default=4)
    return {
        "indent_type": "tabs" if uses_tabs else "spaces",
        "indent_size": size
    }


def docstring_type(doc: str) -> str:
    if not doc:
        return "none"
    return "multi" if "\n" in doc else "single"


def evaluate_style(ast_data: Dict[str, Any], code: str) -> Dict[str, Any]:
    result = {
        "indentation": get_indent_style(code),
        "functions": [],
        "classes": []
    }

    for fn in ast_data.get("functions", []):
        result["functions"].append({
            "name": fn["name"],
            "valid_name": check_snake_case(fn["name"]),
            "doc": docstring_type(fn["doc"])
        })

    for cls in ast_data.get("classes", []):
        cls_info = {
            "name": cls["name"],
            "valid_name": check_pascal_case(cls["name"]),
            "doc": docstring_type(cls["doc"]),
            "methods": []
        }
        for m in cls.get("methods", []):
            cls_info["methods"].append({
                "name": m["name"],
                "valid_name": check_snake_case(m["name"]),
                "doc": docstring_type(m["doc"])
            })
        result["classes"].append(cls_info)

    return result


from pprint import pprint
from style_extractor import parse_file
from style_rules import evaluate_style

code_path = "sample.py"

# Read source code
with open(code_path, "r", encoding="utf-8") as f:
    source_code = f.read()

# Extract code structure from sample.py
structure = parse_file(code_path)

# Analyze style based on extracted structure and source code
style_report = evaluate_style(structure, source_code)

pprint(style_report)