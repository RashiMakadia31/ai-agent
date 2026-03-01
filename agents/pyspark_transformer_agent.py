from agents.base_agent import BaseAgent
from services.llm import call_gemini
 # âœ… switched to Gemini

class PySparkTransformerAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="PySpark Transformer Agent", role_description="Builds transformation logic using PySpark DataFrames or RDDs.")

    def run(self, task_input: str) -> str:
        prompt = f"Write a PySpark solution for the following:\n\n{task_input}"
        return call_gemini(prompt)  # âœ… updated call

