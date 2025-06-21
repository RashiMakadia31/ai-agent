# agents/base_agent.py
class BaseAgent:
    def __init__(self, name: str, role_description: str):
        self.name = name
        self.role_description = role_description

    def run(self, task_input: str) -> str:
        raise NotImplementedError("Each agent must implement the run() method.")
