from agents.base_agent import BaseAgent
from services.llm import call_gemini
  # ✅ switched to Gemini

class SchemaMapperAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Schema Mapper Agent", role_description="Infers and maps schemas in PySpark pipelines.")

    def run(self, task_input: str) -> str:
        prompt = f"Infer and apply PySpark schema for the following data process:\n\n{task_input}"
        return call_gemini(prompt)  # ✅ replaced call_gpt with call_gemini

