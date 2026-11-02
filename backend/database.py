
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def get_connection():
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        return psycopg.connect(database_url)

    return psycopg.connect(
        host="localhost",
        port=5432,
        dbname="hackathon",
        user="hackathon",
        password=os.getenv("POSTGRES_PASSWORD"),
    )
