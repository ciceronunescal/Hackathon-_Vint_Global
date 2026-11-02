
from interpretador import interpretar_solicitacao
from ranking import classificar_colaboradores


def main():
    print("=" * 60)
    print("INHIRE - MOTOR INTELIGENTE DE BUSCA")
    print("=" * 60)

    solicitacao = input("\nO que você procura?\n> ")

    filtros = interpretar_solicitacao(solicitacao)

    skills = filtros["skills"]
    percentual = filtros["percentual"]
    periodo = filtros["periodo"]
    quantidade_candidatos = filtros["quantidade_candidatos"]

    if not skills:
        print("\nNenhuma competência foi identificada.")
        return

    if not periodo:
        print("\nNão foi possível identificar o período.")
        return

    if percentual is None:
        percentual = 0

    print("\nFILTROS IDENTIFICADOS")
    print(f"Competências: {', '.join(skills)}")
    print(f"Disponibilidade mínima: {percentual}%")
    print(f"Período: {periodo}")

    resultados = classificar_colaboradores(
        skills,
        percentual,
        periodo,
        senioridade=filtros.get("senioridade"),
        cargo=filtros.get("cargo"),
    )

    print("\n" + "=" * 60)
    print("RANKING DE COLABORADORES")
    print("=" * 60)

    if not resultados:
        print("\nNenhum colaborador atende aos requisitos.")
        return

    for posicao, colaborador in enumerate(
    resultados[:quantidade_candidatos], 1
):
        print(f"\n{posicao}º - {colaborador['nome']}")
        print(f"Senioridade: {colaborador['senioridade']}")

        print("\nCompetências:")
        for skill, nivel in colaborador["niveis"].items():
            descricao = {
                1: "Básico",
                2: "Intermediário",
                3: "Avançado",
            }.get(nivel, "Não identificado")

            print(f"  {skill}: {descricao}")

        print(
            f"\nExperiência registrada: "
            f"{colaborador['experiencia_meses']} meses"
        )

        print("\nDisponibilidade:")
        for mes in colaborador["disponibilidade"]:
            print(
                f"  {mes['mes']}/{mes['ano']}: "
                f"{mes['disponibilidade']}% livre"
            )
            print(
                f"    Planejamento registrado: "
                f"{'Sim' if mes['possui_planejamento'] else 'Não'}"
            )

        print("-" * 60)

    print(f"\nTotal encontrado: {len(resultados)}")


if __name__ == "__main__":
    main()
