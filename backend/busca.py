
from competencias import buscar_por_competencias
from disponibilidade import calcular_disponibilidade


def buscar_colaboradores(skills, percentual_minimo, periodo):
    candidatos = buscar_por_competencias(skills)
    resultados = []

    for candidato in candidatos:
        disponibilidade_mensal = []
        atende_requisitos = True

        for ano, mes in periodo:
            resultado = calcular_disponibilidade(
                candidato["id"],
                ano,
                mes,
            )

            disponibilidade_mensal.append(resultado)

            if resultado["disponibilidade"] < percentual_minimo:
                atende_requisitos = False
                break

        if atende_requisitos:
            resultados.append({
                "id": candidato["id"],
                "nome": candidato["nome"],
                "senioridade": candidato["senioridade"],
                "cargo": candidato["cargo"],
                "disponibilidade": disponibilidade_mensal,
            })

    return resultados


def main():
    skills = ["Python", "Node.js", "HTML"]
    percentual_minimo = 70

    periodo = [
        (2026, 10),
        (2026, 11),
        (2026, 12),
    ]

    print("\nINHIRE - BUSCA DE PROFISSIONAIS")
    print("=" * 50)

    print(f"Competências: {', '.join(skills)}")
    print(f"Disponibilidade mínima: {percentual_minimo}%")

    colaboradores = buscar_colaboradores(
        skills,
        percentual_minimo,
        periodo,
    )

    print("\nCOLABORADORES COMPATÍVEIS\n")

    for colaborador in colaboradores:
        print(
            f"\n{colaborador['id']} | "
            f"{colaborador['nome']} | "
            f"{colaborador['senioridade']}"
        )

        for mes in colaborador["disponibilidade"]:
            print(
                f"  {mes['mes']}/{mes['ano']}: "
                f"{mes['disponibilidade']}% livre"
            )

    print(f"\nTotal encontrado: {len(colaboradores)}")


if __name__ == "__main__":
    main()
