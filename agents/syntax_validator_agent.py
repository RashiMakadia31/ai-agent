from agents.base_agent import BaseAgent
from services.llm import call_gemini
 # âœ… switched from GPT to Gemini

class SyntaxValidatorAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Syntax Validator Agent", role_description="Validates syntax correctness using parsers or ASTs.")

    def run(self, task_input: str) -> str:
        prompt = f"Check the syntax and structure of the following code:\n\n{task_input}"
        return call_gemini(prompt)  # âœ… updated call method

