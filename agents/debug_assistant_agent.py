from agents.base_agent import BaseAgent
from services.llm import call_gemini
 # âœ… Replace GPT with Gemini
from services.prompt_templates import get_debug_prompt

class DebugAssistantAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Debug Assistant Agent", role_description="Predicts and resolves logical or runtime errors in code.")

    def run(self, task_input: str) -> str:
        prompt = f"{get_debug_prompt()}\n\n{task_input}"
        return call_gemini(prompt)  # âœ… Call Gemini here

