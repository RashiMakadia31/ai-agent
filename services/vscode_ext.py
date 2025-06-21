from fastapi import APIRouter
from pydantic import BaseModel
import subprocess
from core.commands import explain_code, fix_code, generate_code
import os

router = APIRouter()

class VSCodePath(BaseModel):
    path: str
    file_path: str = "None" # Optional

@router.post("/launch-vscode")
def launch_vscode(vscode: VSCodePath):
    try:
        subprocess.Popen([vscode.path])

        if vscode.file_path and os.path.exists(vscode.file_path):
            with open(vscode.file_path, "r", encoding="utf-8") as f:
                code = f.read()

            # You can change this to 'fix_code' or 'generate_code'
            explanation = explain_code(code)
            return {
                "status": "success",
                "message": "VSCode launched and file analyzed.",
                "file_explanation": explanation
            }

        return {"status": "success", "message": "VSCode launched."}

    except FileNotFoundError as e:
        return {"status": "error", "message": f"Invalid path. File not found: {e}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
