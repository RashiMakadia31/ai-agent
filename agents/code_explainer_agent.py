from agents.base_agent import BaseAgent
from services.llm import call_gemini
  # âœ… Updated to use Gemini

class CodeExplainerAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Code Explainer Agent", role_description="Explains what a code snippet does in simple English.")

    def run(self, task_input: str) -> str:
        prompt = f"Explain the following code in simple terms:\n\n{task_input}"
        return call_gemini(prompt)  # âœ… Updated function call

