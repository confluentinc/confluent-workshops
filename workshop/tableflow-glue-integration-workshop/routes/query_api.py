from fastapi import APIRouter
from services.athena_query import execute_athena_query
from services.athena_client import athena_db

router = APIRouter()

@router.get("/api/query-data")
def custom_query(query: str, database: str = athena_db):
    df = execute_athena_query(query, database)
    return {
        "data": df.to_dict('records'),
        "columns": df.columns.tolist(),
        "row_count": len(df)
    }