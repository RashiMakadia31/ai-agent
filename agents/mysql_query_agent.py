from agents.base_agent import BaseAgent
from services.llm import call_gemini
 # ✅ Replace call_gpt with call_gemini
from services.prompt_templates import get_sql_prompt

class MySQLQueryAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="MySQL Query Agent", role_description="Translates natural language into MySQL queries.")

    def run(self, task_input: str) -> str:
        prompt = f"{get_sql_prompt()}\n\n{task_input}"
        return call_gemini(prompt)  # ✅ Updated
