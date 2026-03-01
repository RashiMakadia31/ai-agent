import json
import ast
from difflib import get_close_matches
from core.agent_store import AGENT_MAP
from services.llm import call_gemini

# === SELF-REVIEW FUNCTION ===
def self_review_code(code: str, lang: str) -> str:
    review_prompt = f"""
Review the following {lang.upper()} code for potential issues, anti-patterns, or improvements.
Explain any risks, inefficiencies, or things that could be better in 1â€“3 lines:

\"\"\"{code}\"\"\"
"""
    return call_gemini(review_prompt).strip()


class MasterAgent:
    def __init__(self):
        self.agent_map = AGENT_MAP
        self.user_code_style = ""
        self.thinking_log = []
        self.finished = True
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
            selected = match[0] if match else "python"
            self.thinking_log.append(f"Classified the prompt as '{selected}' based on Gemini response '{response}'.")
            return selected
        except Exception as e:
            self.thinking_log.append(f"âŒ Classification failed: {e}. Defaulting to 'python'.")
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
        self.thinking_log.append("Analyzed user code style and saved style preferences.")

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
            modules = ast.literal_eval(raw_response)
            if isinstance(modules, list):
                self.thinking_log.append(f"Planned the project into modules: {[f for f, _ in modules]}")
                return modules
        except Exception as e:
            self.thinking_log.append(f"âš ï¸ Planning failed: {e}. Using default file 'main.py'.")
            return [("main.py", prompt)]

    def get_agent_for_task(self, task_description: str) -> str:
        routing_prompt = f"""
Select the best agent type for the following task:
Options: [python, sql, pyspark, test, debug, review, validate, schema, comment, mysql]

Task:
\"\"\"{task_description}\"\"\"
Only return one type.
"""
        response = call_gemini(routing_prompt).strip().lower()
        agent = response if response in self.agent_map else "python"
        self.thinking_log.append(f"Selected agent type '{agent}' for task: {task_description}")
        return agent

    def explain_code(self, code: str, filename: str, lang: str) -> str:
        explanation_prompt = f"""
You are a senior developer.

Add clear, professional inline comments to explain each major block of the following {lang.upper()} code from `{filename}`.
Use the user's style:
\"\"\"{self.user_code_style}\"\"\"

Code:
\"\"\"{code}\"\"\"
"""
        explanation = call_gemini(explanation_prompt).strip()
        self.thinking_log.append(f"Generated explanation for `{filename}` in {lang.upper()}.")
        return explanation

    def add_personalized_comments(self, code: str, lang: str) -> str:
        comment_prompt = f"""
You are a personalized code assistant.

Add meaningful comments to the following {lang.upper()} code that match the user's style:
\"\"\"{self.user_code_style}\"\"\"

The comments should:
- Explain intent or edge cases
- Blend into the code naturally
- Avoid generic remarks like "this is a function"
- Be more in number and look professional

Return the full code with comments:
\"\"\"{code}\"\"\"
"""
        commented_code = call_gemini(comment_prompt).strip()
        self.thinking_log.append(f"Added personalized comments to the {lang.upper()} code.")
        return commented_code

    def run(self, prompt: str, user_code_example: str = None, schema: str = None, **kwargs) -> dict:
        # Mark active run state for SSE and clear stale logs from prior calls.
        self.finished = False
        self.thinking_log = []

        # === ETHICAL CHECK (only for pure prompts without code) ===
        if not user_code_example:
            ethical_check_prompt = f"""
You are an AI that strictly evaluates user prompts for safety.

If the following instruction involves illegal activity, unethical behavior, hacking, password cracking, phishing, exploitation, or harmful code â€” respond with a one-line **refusal** and **brief justification**.

If the prompt is safe and ethical, respond with only: OK

Prompt:
\"\"\"{prompt}\"\"\"
"""
            ethical_check_response = call_gemini(ethical_check_prompt, temperature=0.2).strip().lower()

            if ethical_check_response != "ok":
                self.finished = True
                self.thinking_log.append("ðŸš« Ethical violation detected. Refused to process.")
                return {
                    "response": f"âŒ {ethical_check_response}",
                    "thinking_log": self.thinking_log
                }

        if user_code_example:
            self.analyze_user_code_style(user_code_example)

        task_type = self.classify_prompt(prompt)
        final_output = ""

        # === Handle MySQL with schema-aware routing ===
        if task_type == "mysql" and schema:
            try:
                from agents.mysql_query_agent import MySQLQueryAgent
                sql_agent = MySQLQueryAgent()
                generated_code = sql_agent.run(
                    task_input="",  # optional override
                    schema=schema,
                    nl_prompt=prompt,
                    db_cursor=kwargs.get("db_cursor")
                )
                if "âŒ" in generated_code:
                    self.finished = True
                    return {
                        "response": generated_code,
                        "thinking_log": self.thinking_log
                    }
                self.finished = True
                return {
                    "response": f"```sql\n{generated_code}\n```",
                    "thinking_log": self.thinking_log
                }
            except Exception as e:
                self.finished = True
                self.thinking_log.append(f"âŒ MySQL agent failed: {e}")
                return {
                    "response": f"âŒ MySQL query generation failed: {e}",
                    "thinking_log": self.thinking_log
                }

        # === Handle full project (multi-file) ===
        if task_type == "project":
            modules = self.plan_project(prompt)

            for filename, purpose in modules:
                task_prompt = f"Write full code for `{filename}` â€” it should {purpose}"
                agent_type = self.get_agent_for_task(purpose)
                agent = self.agent_map.get(agent_type)

                if not agent:
                    self.thinking_log.append(f"âŒ No agent found for type '{agent_type}'. Skipping file `{filename}`.")
                    continue

                raw_code = agent.run(task_prompt).strip()

                review = self_review_code(raw_code, agent_type)
                self.thinking_log.append(f"ðŸ” Self-review: {review}")

                commented_code = self.add_personalized_comments(raw_code, agent_type)
                final_output += f"# === {filename} ===\n{commented_code}\n\n"

        else:
            agent = self.agent_map.get(task_type)

            if not agent:
                self.finished = True
                self.thinking_log.append(f"âŒ No suitable agent found for task type '{task_type}'.")
                return {
                    "response": "âŒ No suitable agent found.",
                    "thinking_log": self.thinking_log
                }

            raw_code = agent.run(prompt).strip()

            review = self_review_code(raw_code, task_type)
            self.thinking_log.append(f"ðŸ” Self-review: {review}")

            commented_code = self.add_personalized_comments(raw_code, task_type)
            final_output += commented_code.strip()
            self.finished = True

        self.finished = True
        return {
            "response": final_output,
            "thinking_log": self.thinking_log
        }

