from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

try:
    import mysql.connector as mysql_connector
    from mysql.connector import Error as MySQLError
except ModuleNotFoundError:
    mysql_connector = None
    MySQLError = Exception


router = APIRouter()


class MySQLConfig(BaseModel):
    host: str
    user: str
    password: str
    database: str
    port: int = 3306


def _ensure_mysql_connector() -> None:
    if mysql_connector is None:
        raise HTTPException(
            status_code=500,
            detail=(
                "mysql-connector-python is not installed on the server. "
                "Install it with: pip install mysql-connector-python"
            ),
        )


def _format_mysql_schema(config: MySQLConfig) -> str:
    _ensure_mysql_connector()

    connection = None
    cursor = None
    try:
        connection = mysql_connector.connect(
            host=config.host,
            user=config.user,
            password=config.password,
            database=config.database,
            port=config.port,
        )
        cursor = connection.cursor()
        cursor.execute(
            "SELECT TABLE_NAME FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'",
            (config.database,),
        )
        tables = [row[0] for row in cursor.fetchall()]

        schema_lines = []
        for table in tables:
            schema_lines.append(f"Table: {table}")
            cursor.execute(
                "SELECT COLUMN_NAME, COLUMN_TYPE, COLUMN_KEY "
                "FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s",
                (config.database, table),
            )
            for col_name, col_type, col_key in cursor.fetchall():
                key_label = ""
                if col_key == "PRI":
                    key_label = ", PRI Key"
                elif col_key == "MUL":
                    key_label = ", MUL Key"
                schema_lines.append(f"  - {col_name} ({col_type}{key_label})")
            schema_lines.append("")

        return "\n".join(schema_lines).strip()
    except MySQLError as e:
        raise HTTPException(status_code=400, detail=f"MySQL Error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@router.post("/connect-mysql")
def connect_mysql(config: MySQLConfig):
    _ensure_mysql_connector()

    try:
        connection = mysql_connector.connect(
            host=config.host,
            user=config.user,
            password=config.password,
            database=config.database,
            port=config.port,
        )
        if connection.is_connected():
            connection.close()
            return {"status": "success", "message": "Connected to MySQL"}

        raise HTTPException(status_code=500, detail="Failed to connect to MySQL")
    except MySQLError as e:
        raise HTTPException(status_code=400, detail=f"MySQL Error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {str(e)}")


@router.post("/connect-and-schema")
def connect_and_schema(config: MySQLConfig):
    schema = _format_mysql_schema(config)
    return {
        "status": "success",
        "message": "Connected to MySQL and loaded schema.",
        "schema": schema,
    }
