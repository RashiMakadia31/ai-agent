from agents.base_agent import BaseAgent
from services.llm import call_gemini
 # âœ… Switched from call_gpt

class UnitTestWriterAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Unit Test Writer Agent", role_description="Generates unit test cases using unittest or pytest.")

    def run(self, task_input: str) -> str:
        prompt = f"Write Python unit tests for the following code:\n\n{task_input}"
        return call_gemini(prompt)  # âœ… Updated to Gemini

