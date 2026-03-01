from agents.base_agent import BaseAgent
from services.llm import call_gemini

from services.prompt_templates import get_debug_prompt

class CodeReviewerAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Code Reviewer Agent", role_description="Reviews code for bugs, anti-patterns, and improvements.")

    def run(self, task_input: str) -> str:
        prompt = f"{get_debug_prompt()}\n\n{task_input}"
        return call_gemini(prompt)  # âœ… Switched from GPT to Gemini

