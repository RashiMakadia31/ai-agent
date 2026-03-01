from agents.base_agent import BaseAgent
from services.llm import call_gemini
 # âœ… switched from call_gpt to call_gemini
from services.prompt_templates import get_default_prompt

class PythonCodeAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Python Code Agent", role_description="Generates clean, documented Python code.")

    def run(self, task_input: str) -> str:
        prompt = f"{get_default_prompt()}\n\n{task_input}"
        return call_gemini(prompt)  # âœ… updated function call

