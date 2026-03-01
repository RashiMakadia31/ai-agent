from agents.base_agent import BaseAgent
from services.llm import call_gemini
  # âœ… Updated from call_gpt to call_gemini

class BenchmarkAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Benchmark Agent", role_description="Measures runtime or complexity for two versions of code.")

    def run(self, task_input: str) -> str:
        prompt = f"Benchmark the following code or describe which version is faster and why:\n\n{task_input}"
        return call_gemini(prompt)

