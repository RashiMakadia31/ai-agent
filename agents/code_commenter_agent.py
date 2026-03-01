from agents.base_agent import BaseAgent
from services.llm import call_gemini
 # âœ… Updated import

class CodeCommenterAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Code Commenter Agent", role_description="Adds meaningful inline comments to code.")

    def run(self, task_input: str) -> str:
        prompt = f"Add helpful inline comments to this code:\n\n{task_input}"
        return call_gemini(prompt)  # âœ… Updated function call

