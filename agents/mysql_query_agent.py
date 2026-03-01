from agents.base_agent import BaseAgent
from services.llm import call_gemini
 # âœ… Replace call_gpt with call_gemini
from services.prompt_templates import get_sql_prompt

class MySQLQueryAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="MySQL Query Agent", role_description="Translates natural language into MySQL queries.")


    # def run(self, task_input: str, schema: str = None, nl_prompt: str = None, db_cursor=None) -> str:
    #     if schema and nl_prompt:
    #         task_input = (
    #                 get_sql_prompt().strip() +
    #                 "\n\n--- SCHEMA ---\n" +
    #                 schema.strip() +
    #                 "\n--- END SCHEMA ---\n\n"
    #                 "**INSTRUCTIONS:**\n"
    #                 "- Use only the tables and columns from the schema above.\n"
    #                 "- Use exact names as given (including casing).\n"
    #                 "- If a column or table matches the intent of the user's request, use it.\n"
    #                 "- If nothing matches even semantically, respond with:\n"
    #                 "  âŒ 'The requested column/table does not exist in the provided schema.'\n\n"
    #                 "Now generate a MySQL query for the following question:\n" +
    #                 nl_prompt.strip()
    #             )
    #     print("\nðŸ” [DEBUG] Prompt being sent to Gemini:\n", task_input, "\n") 
    #     sql = call_gemini(task_input)

    #     if db_cursor:  # optional runtime SQL validation
    #         try:
    #             db_cursor.execute(sql)
    #             _ = db_cursor.fetchall()  # trigger fetch
    #             return sql
    #         except Exception as e:
    #             print(f"[ERROR] SQL execution failed: {e}")
    #             if schema and nl_prompt:
    #                 from services.prompt_templates import get_sql_fix_prompt
    #                 fix_prompt = get_sql_fix_prompt(nl_prompt, sql, str(e), schema)
    #                 print("\nðŸ” [DEBUG] Sending error + SQL back to Gemini for correction...\n")
    #                 # return call_gemini(fix_prompt)
    #                 fixed_sql = call_gemini(fix_prompt).strip()

    #                 # âœ… If Gemini still returns markdown or extra stuff, sanitize it
    #                 if "âŒ" in fixed_sql:
    #                     return fixed_sql  # return the clear error as-is

    #                 # âœ… If response includes a SQL block, extract it
    #                 if fixed_sql.startswith("```"):
    #                     import re
    #                     fixed_sql = re.sub(r"^```(?:sql)?\s*", "", fixed_sql)
    #                     fixed_sql = re.sub(r"\s*```$", "", fixed_sql)

    #                 # âœ… Return clean result (no explanation or comments)
    #                 return fixed_sql.strip()


    #     return sql


    def run(self, task_input: str, schema: str = None, nl_prompt: str = None, db_cursor=None) -> str:
        if schema and nl_prompt:
            task_input = (
                get_sql_prompt().strip() +
                "\n\n--- SCHEMA ---\n" +
                schema.strip() +
                "\n--- END SCHEMA ---\n\n"
                "**INSTRUCTIONS:**\n"
                "- Use only the tables and columns from the schema above.\n"
                "- Use exact names as given (including casing).\n"
                "- Use semantic reasoning. For example:\n"
                "  'full name' â†’ CustomerName, 'total value' â†’ Amount\n"
                "- Prefer the closest semantic match.\n"
                "- If no semantic match exists, return:\n"
                "  âŒ 'The requested column/table does not exist in the provided schema.'\n\n"
                "Now generate a MySQL query for the following question:\n" +
                nl_prompt.strip()
            )

        print("\nðŸ” [DEBUG] Prompt being sent to Gemini:\n", task_input, "\n")
        sql = call_gemini(task_input)

        if db_cursor:
            try:
                db_cursor.execute(sql)
                _ = db_cursor.fetchall()
                return sql
            except Exception as e:
                print(f"[ERROR] SQL execution failed: {e}")
                if schema and nl_prompt:
                    from services.prompt_templates import get_sql_fix_prompt
                    fix_prompt = get_sql_fix_prompt(nl_prompt, sql, str(e), schema)
                    print("\nðŸ” [DEBUG] Sending error + SQL back to Gemini for correction...\n")
                    fixed_sql = call_gemini(fix_prompt).strip()

                    if "âŒ" in fixed_sql:
                        return fixed_sql

                    if fixed_sql.startswith("```"):
                        import re
                        fixed_sql = re.sub(r"^```(?:sql)?\s*", "", fixed_sql)
                        fixed_sql = re.sub(r"\s*```$", "", fixed_sql)

                    return fixed_sql.strip()

        return sql




