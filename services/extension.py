from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import mysql.connector
import os # Needed for os.environ.get if used in get_mysql_schema_info (less critical for AI, but good for consistent logging if you had it)

# --- Direct Imports of Your Existing AI Agent Components ---
# IMPORTANT: Adjust these import paths based on your actual project structure.
# Example: If MasterAgent is in 'my_project/agents/master_agent.py' and extension.py is in 'my_project/extension_backend/extension.py',
# you might need 'from agents.master_agent import MasterAgent' or similar.
# For simplicity, assuming they are accessible or relative paths.
from agents.master_agent import MasterAgent 
from .mysql_ext import router as mysql_router, MySQLConfig # Assuming mysql_ext.py is in the same directory or accessible

# --- Assuming other core agent dependencies are importable ---
# If your agents/services modules are structured like:
# my_project/
# ├── agents/
# │   └── base_agent.py
# ├── services/
# │   ├── llm.py
# │   └── prompt_templates.py
# └── core/
#     └── agent_store.py
#
# Then MasterAgent's internal imports for these should already work once MasterAgent is imported.
# You generally don't need to re-import them here unless directly used in this file outside the agent's logic.
# -----------------------------------------------------------

app = FastAPI(
    title="MySQL Extension Backend (Consolidated)",
    description="Handles MySQL schema retrieval and directly processes AI requests using MasterAgent."
)

def _get_cors_origins() -> list[str]:
    raw_origins = os.getenv("CORS_ORIGINS", "")
    if raw_origins.strip():
        parsed = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
        if parsed:
            return parsed
    return [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_cors_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the MySQL router from mysql_ext.py
app.include_router(mysql_router, prefix="/mysql")

# Pydantic model for the AI request from frontend
class AIRequest(BaseModel):
    prompt: str
    db_schema: str

# Helper function to get MySQL schema info
def get_mysql_schema_info(config: MySQLConfig):
    schema_info = []
    cnx = None
    try:
        cnx = mysql.connector.connect(
            host=config.host,
            user=config.user,
            password=config.password,
            database=config.database,
            port=config.port
        )
        cursor = cnx.cursor()

        cursor.execute(f"SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = '{config.database}' AND TABLE_TYPE = 'BASE TABLE';")
        tables = [row[0] for row in cursor]

        for table in tables:
            table_details = {'table_name': table, 'columns': []}
            cursor.execute(f"SELECT COLUMN_NAME, COLUMN_TYPE, COLUMN_KEY FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = '{config.database}' AND TABLE_NAME = '{table}';")
            for col_name, col_type, col_key in cursor:
                table_details['columns'].append({
                    'name': col_name,
                    'type': col_type,
                    'is_key': 'PRI' if col_key == 'PRI' else 'MUL' if col_key == 'MUL' else ''
                })
            schema_info.append(table_details)

    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"MySQL Error: {str(err)}")
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"General Error: {str(err)}")
    finally:
        if cnx and cnx.is_connected():
            cursor.close()
            cnx.close()
    
    formatted_schema = ""
    for table in schema_info:
        formatted_schema += f"Table: {table['table_name']}\n"
        for col in table['columns']:
            formatted_schema += f"  - {col['name']} ({col['type']}"
            if col['is_key']:
                formatted_schema += f", {col['is_key']} Key"
            formatted_schema += ")\n"
    formatted_schema += "\n"
    return formatted_schema

@app.post("/connect-and-schema")
async def connect_and_schema_endpoint(config: MySQLConfig):
    """
    Connects to MySQL, retrieves and returns the database schema.
    This endpoint is called by extension_ui.js.
    """
    try:
        schema = get_mysql_schema_info(config)
        return {"status": "success", "schema": schema, "message": "Schema retrieved"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process schema request: {str(e)}")

@app.post("/ask-ai")
async def ask_ai_assistant(request: AIRequest):
    """
    Receives the user's natural language prompt and schema from the frontend.
    Directly uses the MasterAgent to process the request and generate SQL.
    This endpoint is called by extension_ui.js.
    """
    if not request.schema:
        raise HTTPException(status_code=400, detail="Schema is required for AI query.")

    try:
        # Construct a comprehensive prompt that includes the schema.
        # Your MasterAgent and MySQLQueryAgent must be able to interpret this format.
        full_ai_prompt_with_schema = (
            f"User query: {request.prompt}\n\n"
            f"Database Schema:\n```\n{request.schema}\n```\n\n"
            f"Generate a MySQL SQL query based on the above." # Add a clear instruction for your agent
        )
        
        # Instantiate your MasterAgent
        master_agent = MasterAgent() 
        
        # Run the MasterAgent with the enriched prompt.
        # MasterAgent.run() will internally classify, route, and generate code.
        # The output of MasterAgent.run() should be the generated SQL string or structured response.
        
        # This call will trigger the MasterAgent to classify the prompt (which now includes schema),
        # route it to the SQL agent, and get the SQL response.
        # Assuming MasterAgent.run() can handle this combined prompt and return the final SQL.
        agent_result = master_agent.run(prompt=full_ai_prompt_with_schema)
        if isinstance(agent_result, dict):
            ai_response_text = str(agent_result.get("response", "")).strip()
        else:
            ai_response_text = str(agent_result).strip()

        # The MasterAgent.run method usually returns formatted output including explanations and code blocks.
        # We need to extract just the SQL part.
        # This is a generic way to extract content from markdown code blocks.
        suggested_sql = ""
        # Look for a code block starting with ```sql or ```
        if "```sql" in ai_response_text:
            start_index = ai_response_text.find("```sql") + len("```sql")
            end_index = ai_response_text.find("```", start_index)
            if start_index != -1 and end_index != -1:
                suggested_sql = ai_response_text[start_index:end_index].strip()
        elif "```" in ai_response_text: # Generic markdown code block
            start_index = ai_response_text.find("```") + len("```")
            end_index = ai_response_text.find("```", start_index)
            if start_index != -1 and end_index != -1:
                suggested_sql = ai_response_text[start_index:end_index].strip()
        else:
            # If no code block found, assume the entire response is the SQL or an error/plain text
            suggested_sql = ai_response_text.strip()


        if not suggested_sql or "SELECT * FROM some_schema_aware_table WHERE condition;" in suggested_sql:
            # This is a check for the placeholder response from your agent if it's not fully integrated yet.
            # You might want to remove or refine this check once your agent is fully functional.
            print(f"Warning: AI agent returned a placeholder or unexpected response: {ai_response_text[:100]}...")
            suggested_sql = "⚠️ AI could not generate specific SQL. Please refine your query or check agent's logic."


        print("SQL generated by MasterAgent directly.")
        return {"status": "success", "response": suggested_sql}

    except Exception as e:
        print(f"Error processing AI request in extension.py: {e}")
        raise HTTPException(status_code=500, detail=f'Failed to generate SQL via MasterAgent: {str(e)}')

if __name__ == "__main__":
    import uvicorn
    # This is the port for the Extension Backend (which now includes AI logic)
    uvicorn.run(app, host="0.0.0.0", port=5001, reload=True)
