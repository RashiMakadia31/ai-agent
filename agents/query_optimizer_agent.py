from agents.base_agent import BaseAgent
from services.llm import call_gemini
  # âœ… switched from call_gpt to call_gemini

class QueryOptimizerAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Query Optimizer Agent", role_description="Optimizes SQL and PySpark queries using indexing and execution plans.")

    def run(self, task_input: str) -> str:
        prompt = f"Optimize the following SQL or PySpark query for performance:\n\n{task_input}"
        return call_gemini(prompt)  # âœ… updated to use Gemini

