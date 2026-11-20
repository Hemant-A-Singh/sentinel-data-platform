import os
from dotenv import load_dotenv

load_dotenv()

class PGSQLConfig:
    PG_HOST = os.getenv("SENTINEL_DB_HOST", "localhost")
    PG_PORT = int(os.getenv("SENTINEL_DB_PORT", "5433"))
    PG_USER = os.getenv("POSTGRES_USER")
    PG_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    PG_DB = os.getenv("POSTGRES_DB")


pg_config = PGSQLConfig()