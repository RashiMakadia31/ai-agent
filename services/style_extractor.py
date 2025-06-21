import ast
from typing import List, Dict, Any


class StyleExtractor(ast.NodeVisitor):
    def __init__(self):
        self.result = {
            "module_doc": None,
            "functions": [],
            "classes": []
        }

    def visit_Module(self, node):
        self.result["module_doc"] = ast.get_docstring(node)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        if isinstance(getattr(node, 'parent', None), ast.Module):
            self.result["functions"].append({
                "name": node.name,
                "doc": ast.get_docstring(node),
                "args": [arg.arg for arg in node.args.args]
            })
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        class_data = {
            "name": node.name,
            "doc": ast.get_docstring(node),
            "methods": []
        }
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                class_data["methods"].append({
                    "name": item.name,
                    "doc": ast.get_docstring(item),
                    "args": [arg.arg for arg in item.args.args]
                })
        self.result["classes"].append(class_data)
        self.generic_visit(node)


def add_parents(tree):
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            child.parent = node


def parse_code(src: str) -> Dict[str, Any]:
    tree = ast.parse(src)
    add_parents(tree)
    extractor = StyleExtractor()
    extractor.visit(tree)
    return extractor.result


def parse_file(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        code = f.read()
    return parse_code(code)


from pprint import pprint
from style_extractor import parse_file

pprint(parse_file("sample.py"))