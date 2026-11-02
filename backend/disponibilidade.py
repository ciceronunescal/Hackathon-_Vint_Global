
from datetime import date

from database import get_connection


MONTHS = {
    1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr",
    5: "Mai", 6: "Jun", 7: "Jul", 8: "Ago",
    9: "Set", 10: "Out", 11: "Nov", 12: "Dez",
}



def calcular_disponibilidade(colaborador_id, ano, mes):
    query = """
        SELECT
            COALESCE(SUM(p.porcentagem), 0) AS total_alocado,
            COUNT(*) AS total_planejamentos
        FROM "InHire".alocacoes a
        INNER JOIN "InHire".planejamentos p
            ON p.id_alocacao = a.id
        WHERE a.id_colaborador = %s
          AND a.status = TRUE
          AND a.deletado IS DISTINCT FROM TRUE
          AND p.status = TRUE
          AND p.deletado IS DISTINCT FROM TRUE
          AND p.ano = %s
          AND p.mes = %s
    """

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                query,
                (colaborador_id, ano, MONTHS[mes]),
            )

            alocacao, total_planejamentos = cursor.fetchone()

    disponibilidade = 100 - alocacao
    possui_planejamento = total_planejamentos > 0

    return {
        "ano": ano,
        "mes": MONTHS[mes],
        "alocacao": alocacao,
        "disponibilidade": disponibilidade,
        "sobrealocado": alocacao > 100,
        "possui_planejamento": possui_planejamento,
        "situacao": (
            "COM_PLANEJAMENTO"
            if possui_planejamento
            else "SEM_PLANEJAMENTO"
        ),
    }


def proximos_meses(quantidade=3):
    hoje = date.today()
    meses = []

    for indice in range(quantidade):
        total = hoje.year * 12 + hoje.month - 1 + indice
        ano = total // 12
        mes = total % 12 + 1
        meses.append((ano, mes))

    return meses


if __name__ == "__main__":
    colaborador_id = int(input("ID do colaborador: "))

    print("\nDISPONIBILIDADE MENSAL\n")

    for ano, mes in proximos_meses():
        resultado = calcular_disponibilidade(
            colaborador_id, ano, mes
        )

        print(
            f"{resultado['mes']}/{resultado['ano']} | "
            f"Alocado: {resultado['alocacao']}% | "
            f"Disponível: {resultado['disponibilidade']}%"
        )

        if resultado["sobrealocado"]:
            print("  ATENÇÃO: colaborador sobrealocado!")
