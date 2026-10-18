
import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv(Path(__file__).resolve().parent / ".env")

connection_string = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    f"SERVER={os.getenv('SQL_SERVER_HOST', 'localhost')},"
    f"{os.getenv('SQL_SERVER_PORT', '1433')};"
    f"DATABASE={os.getenv('SQL_SERVER_DATABASE', 'ColdChainLogistics')};"
    f"UID={os.getenv('SQL_ADMIN_USER')};"
    f"PWD={os.getenv('SQL_ADMIN_PASSWORD')};"
    "Encrypt=no;"
    "TrustServerCertificate=yes;"
)

engine = create_engine(
    "mssql+pyodbc:///?odbc_connect=" + quote_plus(connection_string)
)

try:
    with engine.connect() as connection:
        database = connection.execute(text("SELECT DB_NAME()")).scalar()
        print(f"Connection successful! Database: {database}")
except Exception as error:
    print(f"Connection failed: {error}")
finally:
    engine.dispose()
