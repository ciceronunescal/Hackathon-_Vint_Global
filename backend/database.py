
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv


# Carrega o .env da pasta principal do projeto
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)


def get_connection():
    return psycopg.connect(
        host="localhost",
        port=5432,
        dbname="hackathon",
        user="hackathon",
        password=os.getenv("POSTGRES_PASSWORD"),
    )


def test_connection():
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT current_database(), current_user")
                result = cursor.fetchone()

                print("Conexão realizada com sucesso!")
                print(f"Banco: {result[0]}")
                print(f"Usuário: {result[1]}")

    except psycopg.Error as error:
        print(f"Erro ao conectar: {error}")


if __name__ == "__main__":
    test_connection()
