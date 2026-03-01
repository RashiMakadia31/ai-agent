from agents.base_agent import BaseAgent
from services.llm import call_gemini
 # âœ… Use Gemini instead of GPT

class NaturalLanguageToCodeAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Natural Language to Code Agent", role_description="Converts plain English tasks into valid code.")

    def run(self, task_input: str) -> str:
        prompt = f"Write code for the following natural language task:\n\n{task_input}"
        return call_gemini(prompt)  # âœ… Updated call

