import json
from difflib import get_close_matches
from core.agent_store import AGENT_MAP
from services.llm import call_gemini


class MasterAgent:
    def __init__(self):
        self.agent_map = AGENT_MAP
        self.user_code_style = ""

    def classify_prompt(self, prompt: str) -> str:
        valid_types = list(self.agent_map.keys()) + ["project"]

        classify_prompt = f"""
Classify the following user request into one of these types:
[{", ".join(valid_types)}]

User prompt:
\"\"\"{prompt}\"\"\"
Only return one word from the list.
"""

        try:
            response = call_gemini(classify_prompt).strip().lower()
            match = get_close_matches(response, valid_types, n=1, cutoff=0.7)
            return match[0] if match else "python"
        except Exception as e:
            print(f"[ERROR] Classification failed: {e}")
            return "python"

    def analyze_user_code_style(self, code: str):
        style_prompt = f"""
Analyze the following user code and extract the coding style features like:
- Naming conventions
- Comment tone and frequency
- Formatting choices (spaces, line breaks)
- Typical structure and logic flow

Summarize these patterns in plain text:
\"\"\"{code}\"\"\"
"""
        self.user_code_style = call_gemini(style_prompt).strip()

    def plan_project(self, prompt: str) -> list:
        planner_prompt = f"""
You are a project planner.

Break down the following prompt into individual code files (modules), with purpose for each.

Return as a Python list of (filename, purpose) tuples.

Prompt:
\"\"\"{prompt}\"\"\"
"""
        try:
            raw_response = call_gemini(planner_prompt)
            return eval(raw_response) if isinstance(eval(raw_response), list) else []
        except:
            return [("main.py", prompt)]

    def get_agent_for_task(self, task_description: str) -> str:
        routing_prompt = f"""
Select the best agent type for the following task:
Options: [python, sql, pyspark, test, debug, review, validate, schema, comment]

Task:
\"\"\"{task_description}\"\"\"
Only return one type.
"""
        response = call_gemini(routing_prompt).strip().lower()
        return response if response in self.agent_map else "python"

    def generate_commented_code(self, prompt: str, lang: str) -> str:
        commented_code_prompt = f"""
Write {lang.upper()} code for the following task.

Ensure the code includes **in-line comments** that clearly explain each line or section so it's easy to understand for learners.

Prompt:
\"\"\"{prompt}\"\"\"
"""
        return call_gemini(commented_code_prompt).strip()

    def run(self, prompt: str, user_code_example: str = None) -> str:
        if user_code_example:
            self.analyze_user_code_style(user_code_example)

        task_type = self.classify_prompt(prompt)

        if task_type == "project":
            modules = self.plan_project(prompt)
            final_output = ""

            for filename, purpose in modules:
                task_prompt = f"{purpose}"
                agent_type = self.get_agent_for_task(purpose)
                agent = self.agent_map.get(agent_type)
                if not agent:
                    continue

                # Instead of plain code, generate code with in-line comments
                commented_code = self.generate_commented_code(task_prompt, agent_type)
                explanation = self.explain_code(commented_code, filename, agent_type)

                final_output += f"### 📄 {filename}: {purpose}\n"
                final_output += f"🧠 **Explanation:**\n{explanation}\n\n"
                code_block = f"```{agent_type}\n{commented_code}\n```"
                final_output += code_block + "\n\n"

            return final_output.strip()

        else:
            agent = self.agent_map.get(task_type)
            if not agent:
                return "❌ No suitable agent found."

            # Instead of plain code, generate code with in-line comments
            commented_code = self.generate_commented_code(prompt, task_type)
            explanation = self.explain_code(commented_code, "task", task_type)

            return f"""🧠 **Explanation:**\n{explanation}\n\n```{task_type}\n{commented_code}\n```"""

    def explain_code(self, code: str, filename: str, lang: str) -> str:
        explanation_prompt = f"""
You are a senior developer.

Explain the following {lang.upper()} code from `{filename}` in a clear and professional way. 
Explain what the code does overall, and how each major block contributes to the functionality.

Code:
\"\"\"{code}\"\"\"
"""
        return call_gemini(explanation_prompt).strip()
