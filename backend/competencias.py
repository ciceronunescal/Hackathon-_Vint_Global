
from psycopg.rows import dict_row

from database import get_connection



def buscar_por_competencias(skills):
    query = """
        SELECT
            c.id,
            c.nome_abreviado AS nome,
            senioridade.valor_dominio AS senioridade,
            cargo.valor_dominio AS cargo,
            COUNT(DISTINCT s.id) AS skills_encontradas

        FROM "InHire".colaboradores c

        INNER JOIN "InHire".colaborador_skills cs
            ON cs.id_colaborador = c.id

        INNER JOIN "InHire".skills s
            ON s.id = cs.id_skill

        LEFT JOIN "InHire".dominios senioridade
            ON senioridade.id = c.id_senioridade

        LEFT JOIN "InHire".dominios cargo
            ON cargo.id = c.id_cargo

        WHERE c.status = TRUE
          AND c.deletado IS DISTINCT FROM TRUE
          AND cs.status = TRUE
          AND cs.deletado IS DISTINCT FROM TRUE
          AND LOWER(s.nome_skill) = ANY(%s)

        GROUP BY
            c.id,
            c.nome_abreviado,
            senioridade.valor_dominio,
            cargo.valor_dominio

        HAVING COUNT(DISTINCT LOWER(s.nome_skill)) = %s

        ORDER BY c.nome_abreviado
    """

    skills_normalizadas = [
        skill.strip().lower() for skill in skills
    ]

    skills_normalizadas = list(
        dict.fromkeys(skills_normalizadas)
    )

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                query,
                (
                    skills_normalizadas,
                    len(skills_normalizadas),
                ),
            )

            return cursor.fetchall()



if __name__ == "__main__":
    skills = ["Python", "Node.js", "HTML"]

    colaboradores = buscar_por_competencias(skills)

    print("\nCOLABORADORES COMPATÍVEIS\n")

    for colaborador in colaboradores:
        print(
            f"{colaborador['id']} | "
            f"{colaborador['nome']} | "
            f"{colaborador['senioridade']}"
        )

    print(f"\nTotal encontrado: {len(colaboradores)}")
