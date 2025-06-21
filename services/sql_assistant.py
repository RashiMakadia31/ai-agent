from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
import logging


router = APIRouter()
logger = logging.getLogger(__name__)


class QueryRequest(BaseModel):
    natural_language: str
    database_type: Optional[str] = "mysql"  


class QueryResponse(BaseModel):
    sql_query: str
    result_preview: Optional[list] = None


@router.post("/generate-sql", response_model=QueryResponse)
async def generate_sql(request: QueryRequest):
    try:
        logger.info(f"Received query request: {request.natural_language}")

        sql_query = f"SELECT * FROM users WHERE name = '{request.natural_language}';"

        return QueryResponse(
            sql_query=sql_query,
            result_preview=[]  
        )

    except Exception as e:
        logger.error(f"Error in generating SQL: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate SQL query")


@router.get("/health")
async def health_check():
    return {"status": "SQL Assistant API is up and running!"}