from core.agent_store import AGENT_MAP

class MasterAgent:
    def __init__(self):
        self.agent_map = AGENT_MAP

    def classify_task(self, prompt: str) -> str:
        prompt_lower = prompt.lower()

        if "select" in prompt_lower or "sql" in prompt_lower:
            return "mysql"
        elif "pyspark" in prompt_lower or "rdd" in prompt_lower:
            return "pyspark"
        elif "unit test" in prompt_lower or "test case" in prompt_lower:
            return "test"
        elif "schema" in prompt_lower:
            return "schema"
        elif "optimize" in prompt_lower or "optimization" in prompt_lower:
            return "optimize"
        elif "debug" in prompt_lower or "error" in prompt_lower:
            return "debug"
        elif "review" in prompt_lower:
            return "review"
        elif "explain" in prompt_lower:
            return "explain"
        elif "comment" in prompt_lower:
            return "comment"
        elif "validate" in prompt_lower or "syntax" in prompt_lower:
            return "validate"
        elif "benchmark" in prompt_lower or "compare" in prompt_lower:
            return "benchmark"
        elif "translate" in prompt_lower or "natural language" in prompt_lower:
            return "nl_to_code"
        else:
            return "python"

    def run(self, prompt: str) -> str:
        task_type = self.classify_task(prompt)
        agent = self.agent_map.get(task_type)

        if not agent:
            return f"⚠️ No agent found for task type: {task_type}"

        print(f"✅ Using agent: {task_type}")
        return agent.run(prompt)
