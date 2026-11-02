
from datetime import date

from database import get_connection


def calcular_experiencia(colaborador_id):
    hoje = date.today()

    query = """
        WITH meses_validos AS (
            SELECT DISTINCT
                p.ano,
                CASE p.mes
                    WHEN 'Jan' THEN 1
                    WHEN 'Fev' THEN 2
                    WHEN 'Mar' THEN 3
                    WHEN 'Abr' THEN 4
                    WHEN 'Mai' THEN 5
                    WHEN 'Jun' THEN 6
                    WHEN 'Jul' THEN 7
                    WHEN 'Ago' THEN 8
                    WHEN 'Set' THEN 9
                    WHEN 'Out' THEN 10
                    WHEN 'Nov' THEN 11
                    WHEN 'Dez' THEN 12
                END AS numero_mes
            FROM "InHire".alocacoes a
            JOIN "InHire".planejamentos p
                ON p.id_alocacao = a.id
            WHERE a.id_colaborador = %s
              AND a.deletado IS DISTINCT FROM TRUE
              AND p.deletado IS DISTINCT FROM TRUE
              AND p.status = TRUE
              AND p.porcentagem > 0
        )
        SELECT COUNT(*)
        FROM meses_validos
        WHERE ano < %s
           OR (ano = %s AND numero_mes <= %s)
    """

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                query,
                (
                    colaborador_id,
                    hoje.year,
                    hoje.year,
                    hoje.month,
                ),
            )

            return cursor.fetchone()[0]


if __name__ == "__main__":
    colaborador_id = int(input("Digite o ID do colaborador: "))

    meses = calcular_experiencia(colaborador_id)

    anos = meses // 12
    meses_restantes = meses % 12

    print(f"\nColaborador ID: {colaborador_id}")
    print(f"Experiência registrada: {meses} meses")
    print(f"Equivalente a: {anos} ano(s) e {meses_restantes} mês(es)")