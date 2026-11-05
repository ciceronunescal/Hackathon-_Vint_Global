import unicodedata
from collections import defaultdict

from psycopg.rows import dict_row

from busca import buscar_colaboradores
from database import get_connection
from experiencia import calcular_experiencia


SENIORIDADES = {
    "TRAINEE": 1,
    "JUNIOR": 2,
    "PLENO": 3,
    "SENIOR": 4,
}

NIVEIS = {
    "BASICO": 1,
    "INTERMEDIARIO": 2,
    "AVANCADO": 3,
}


def normalizar(texto):
    texto = unicodedata.normalize("NFKD", str(texto or ""))
    texto = "".join(
        letra for letra in texto
        if not unicodedata.combining(letra)
    )
    return texto.strip().upper()


def consultar_niveis(colaboradores, skills):
    if not colaboradores:
        return {}

    ids = [c["id"] for c in colaboradores]
    skills_normalizadas = {normalizar(skill) for skill in skills}

    query = """
        SELECT
            cs.id_colaborador,
            s.nome_skill,
            d.valor_dominio AS nivel
        FROM "InHire".colaborador_skills cs
        JOIN "InHire".skills s
            ON s.id = cs.id_skill
        LEFT JOIN "InHire".dominios d
            ON d.id = cs.id_nivel_conhecimento
        WHERE cs.id_colaborador = ANY(%s)
          AND cs.status = TRUE
          AND cs.deletado IS DISTINCT FROM TRUE
    """

    niveis = defaultdict(dict)

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute(query, (ids,))

            for registro in cursor.fetchall():
                nome_skill = normalizar(registro["nome_skill"])

                if nome_skill not in skills_normalizadas:
                    continue

                id_colaborador = registro["id_colaborador"]
                nivel = NIVEIS.get(
                    normalizar(registro["nivel"]), 0
                )

                anterior = niveis[id_colaborador].get(nome_skill, 0)
                niveis[id_colaborador][nome_skill] = max(anterior, nivel)

    return dict(niveis)


def classificar_colaboradores(
    skills, percentual, periodo,
    senioridade=None, cargo=None
):
    candidatos = buscar_colaboradores(skills, percentual, periodo)

    if senioridade:
        candidatos = [
            candidato
            for candidato in candidatos
            if normalizar(candidato["senioridade"])
            == normalizar(senioridade)
        ]

    if cargo:
        candidatos = [
            candidato
            for candidato in candidatos
            if normalizar(candidato["cargo"])
            == normalizar(cargo)
        ]

    if not candidatos:
        return []

    niveis = consultar_niveis(candidatos, skills)
    resultados = []

    for candidato in candidatos:
        identificador = candidato["id"]
        competencias = niveis.get(identificador, {})

        pontuacoes = [
            competencias.get(normalizar(skill), 0)
            for skill in skills
        ]

        meses = candidato["disponibilidade"]
        disponibilidades = [
            float(mes["disponibilidade"])
            for mes in meses
        ]

        # Conta somente os meses que possuem planejamento registrado.
        # Isso nao altera a disponibilidade calculada nem exclui candidatos.
        meses_com_planejamento = sum(
            1 for mes in meses
            if mes.get("possui_planejamento") is True
        )

        experiencia = calcular_experiencia(identificador)

        resultado = {
            **candidato,
            "niveis": {
                skill: competencias.get(normalizar(skill), 0)
                for skill in skills
            },
            "senioridade_pontos": SENIORIDADES.get(
                normalizar(candidato["senioridade"]), 0
            ),
            "competencia_minima": min(pontuacoes, default=0),
            "competencia_total": sum(pontuacoes),
            "experiencia_meses": experiencia,
            "disponibilidade_minima": min(disponibilidades, default=0),
            "disponibilidade_media": (
                sum(disponibilidades) / len(disponibilidades)
                if disponibilidades else 0
            ),
            "meses_com_planejamento": meses_com_planejamento,
            "meses_sem_planejamento": len(meses) - meses_com_planejamento,
        }

        resultados.append(resultado)

    # Ordem de classificacao:
    # 1. Melhor nivel minimo entre as competencias exigidas.
    # 2. Maior soma dos niveis das competencias exigidas.
    # 3. Maior disponibilidade no mes mais restritivo.
    # 4. Mais meses com planejamento registrado.
    # 5. Maior experiencia em projetos.
    # 6. Maior senioridade (desempate, se nao houver filtro).
    # 7. Maior disponibilidade media.
    # 8. Nome, para uma ordem estavel.
    #
    # Cargo e senioridade informados continuam sendo filtros obrigatorios.
    resultados.sort(
        key=lambda c: (
            -c["competencia_minima"],
            -c["competencia_total"],
            -c["disponibilidade_minima"],
            -c["meses_com_planejamento"],
            -c["experiencia_meses"],
            -c["senioridade_pontos"],
            -c["disponibilidade_media"],
            c["nome"],
        )
    )

    return resultados


def main():
    skills = ["Python", "Node.js", "HTML"]
    percentual = 70

    periodo = [
        (2026, 10),
        (2026, 11),
        (2026, 12),
    ]

    print("\n" + "=" * 60)
    print("INHIRE - RANKING DE PROFISSIONAIS")
    print("=" * 60)

    print(f"Skills: {', '.join(skills)}")
    print(f"Disponibilidade minima: {percentual}%")

    resultados = classificar_colaboradores(skills, percentual, periodo)

    if not resultados:
        print("\nNenhum colaborador atende aos requisitos.")
        return

    for posicao, colaborador in enumerate(resultados, 1):
        experiencia = colaborador["experiencia_meses"]

        print(f"\n{'-' * 60}")
        print(f"{posicao}º - {colaborador['nome']}")
        print(f"ID: {colaborador['id']}")
        print(f"Senioridade: {colaborador['senioridade']}")
        print(
            f"Experiencia: {experiencia // 12} ano(s) "
            f"e {experiencia % 12} mes(es)"
        )
        print(
            "Meses com planejamento registrado: "
            f"{colaborador['meses_com_planejamento']}"
        )

        print("Competencias:")

        for skill, nivel in colaborador["niveis"].items():
            descricao = {
                1: "Basico",
                2: "Intermediario",
                3: "Avancado",
            }.get(nivel, "Nao identificado")
            print(f"  {skill}: {descricao}")

        print("Disponibilidade:")
        for mes in colaborador["disponibilidade"]:
            print(
                f"  {mes['mes']}/{mes['ano']}: "
                f"{mes['disponibilidade']}% livre"
            )

    print(f"\nTotal de candidatos: {len(resultados)}")


if __name__ == "__main__":
    main()