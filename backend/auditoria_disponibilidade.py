
from collections import defaultdict

from psycopg.rows import dict_row

from database import get_connection


def auditar_disponibilidade(colaborador_id, periodo):
    query = """
        SELECT
            a.id AS id_alocacao,
            a.id_demanda,
            d.nome_demanda,
            a.status AS status_alocacao,
            a.deletado AS alocacao_excluida,
            p.ano,
            p.mes,
            p.porcentagem,
            p.status AS status_planejamento,
            p.deletado AS planejamento_excluido
        FROM "InHire".alocacoes a
        LEFT JOIN "InHire".demandas d
            ON d.id = a.id_demanda
        LEFT JOIN "InHire".planejamentos p
            ON p.id_alocacao = a.id
        WHERE a.id_colaborador = %s
        ORDER BY a.id, p.ano, p.mes
    """

    meses = {
        1: "Jan", 2: "Fev", 3: "Mar",
        4: "Abr", 5: "Mai", 6: "Jun",
        7: "Jul", 8: "Ago", 9: "Set",
        10: "Out", 11: "Nov", 12: "Dez",
    }

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute(query, (colaborador_id,))
            registros = cursor.fetchall()

    agrupados = defaultdict(list)

    for registro in registros:
        if registro["ano"] is None:
            continue

        for ano, mes in periodo:
            if (
                registro["ano"] == ano
                and registro["mes"] == meses[mes]
            ):
                agrupados[(ano, mes)].append(registro)

    for ano, mes in periodo:
        print(f"\n{'=' * 55}")
        print(f"{meses[mes]}/{ano}")
        print("=" * 55)

        registros_mes = agrupados[(ano, mes)]
        comprometido = 0
        validos = 0

        if not registros_mes:
            print("Nenhum planejamento encontrado.")
            print("Disponibilidade presumida: 100%")
            continue

        for registro in registros_mes:
            valido = (
                registro["status_alocacao"] is True
                and registro["alocacao_excluida"] is not True
                and registro["status_planejamento"] is True
                and registro["planejamento_excluido"] is not True
            )

            print(
                f"\nDemanda: {registro['nome_demanda']}"
                f"\nAlocação ID: {registro['id_alocacao']}"
                f"\nPercentual: {registro['porcentagem']}%"
                f"\nStatus alocação: {registro['status_alocacao']}"
                f"\nExcluída: {registro['alocacao_excluida']}"
                f"\nStatus planejamento: {registro['status_planejamento']}"
                f"\nPlanejamento excluído: "
                f"{registro['planejamento_excluido']}"
                f"\nConsiderado no cálculo: {valido}"
            )

            if valido:
                comprometido += registro["porcentagem"] or 0
                validos += 1

        print(f"\nTotal comprometido: {comprometido}%")
        print(f"Disponibilidade calculada: {100 - comprometido}%")

        if validos == 0:
            print("ATENÇÃO: nenhum planejamento válido encontrado.")

        if comprometido > 100:
            print("ATENÇÃO: sobrealocação identificada.")


if __name__ == "__main__":
    colaborador_id = int(input("ID do colaborador: "))

    periodo = [
        (2026, 10),
        (2026, 11),
        (2026, 12),
    ]

    auditar_disponibilidade(colaborador_id, periodo)
