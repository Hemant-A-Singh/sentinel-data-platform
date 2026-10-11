import psycopg2
#import pandas as pd
import os
from dotenv import load_dotenv
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()

file = "/mnt/c/Users/heman/Downloads/raw_orders.csv"

def connect():
    try:
        conn = psycopg2.connect(
                        host = os.getenv("POSTGRES_HOST"),
                        port = int(os.getenv("POSTGRES_PORT",5433)),
                        user = os.getenv("POSTGRES_USER"),
                        password = os.getenv("POSTGRES_PASSWORD"),
                        database = os.getenv("POSTGRES_DB")
                        )
        conn.autocommit = False
        logger.info("Connection to the database established successfully.")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to the database: {e}")
        raise e

def disconnect(conn):
    if conn:
        conn.close()
        logger.info("Database connection closed.")

def execute_sql_file(file_path:str,conn):
    #cursor = conn.cursor()
    sql_text = Path(file_path).read_text()
    statement = [text.strip() for text in sql_text.split(";") if text.strip()]

    try:
        if not statement:
            logger.info("No sql queries to execute")
            return
        
        with conn.cursor() as cursor:
            for i,stmt in enumerate(statement):
                cursor.execute(stmt)
                logger.info(f"Statement {i+1} executed successfully.")
        
    except Exception as e:
            logger.error(f"Error executing statement: {e}")
            raise

def load_raw_data(file_path:str,target_table:str, conn):
    
    #cursor = conn.cursor()
    sql_text = f"""
                    COPY {target_table}
                        FROM STDIN WITH
                        (
                        FORMAT CSV,
                        HEADER TRUE,
                        DELIMITER ',',
                        NULL ''
                        )
                    """
    try:  
        with conn.cursor() as cursor:
            with open(file_path,"r",encoding="utf-8") as f:
                cursor.copy_expert(sql_text,f)
        logger.info(f"data loaded into {target_table} successfully")

    except Exception as e:
        logger.error(f"Data failed to load: {e}")
        raise
    
def main():
    conn = connect()
    try:
        execute_sql_file(file_path="sql/raw_orders.sql", conn=conn)
        
        load_raw_data(file_path=file, target_table="raw_orders", conn=conn)

        execute_sql_file(file_path="sql/transform_orders.sql", conn=conn)

        conn.commit()
        logger.info("Data transformation completed successfully.")

    except Exception as e:
        conn.rollback()
        logger.error(f"An error occurred: {e}")
        raise
    finally:
        disconnect(conn)

if __name__ == "__main__":
    main()

        



