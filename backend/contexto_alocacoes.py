
import calendar
import unicodedata
from collections import defaultdict
from datetime import date

from database import get_connection


MESES = {
    "jan": 1,
    "fev": 2,
    "mar": 3,
    "abr": 4,
    "mai": 5,
    "jun": 6,
    "jul": 7,
    "ago": 8,
    "set": 9,
    "out": 10,
    "nov": 11,
    "dez": 12,
}


def converter_mes(valor):
    if valor is None:
        return None

    texto = str(valor).strip().lower()

    texto = "".join(
        caractere
        for caractere in unicodedata.normalize("NFD", texto)
        if not unicodedata.combining(caractere)
    )

    texto = texto.replace(".", "")

    if texto.isdigit():
        numero = int(texto)
        return numero if 1 <= numero <= 12 else None

    return MESES.get(texto[:3])


def consultar_contexto_alocacoes(id_colaborador, periodo):
    """
    Consulta as demandas em vigencia e seus planejamentos.

    Nao modifica a disponibilidade calculada
    pelo InHire.

    Retorna um dicionario por ano e mes.
    """

    sql = """
        SELECT
            a.id,
            d.id,
            d.nome_demanda,
            d.dt_inicio_demanda,
            d.dt_termino_demanda_prevista,
            p.mes,
            p.ano,
            p.porcentagem

        FROM "InHire".alocacoes a

        JOIN "InHire".demandas d
            ON d.id = a.id_demanda

        LEFT JOIN "InHire".planejamentos p
            ON p.id_alocacao = a.id
            AND p.status IS TRUE
            AND p.deletado IS FALSE

        WHERE a.id_colaborador = %s
          AND a.status IS TRUE
          AND a.deletado IS FALSE
          AND d.status IS TRUE
          AND d.deletado IS FALSE

        ORDER BY d.id, a.id
    """

    with get_connection() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(sql, (id_colaborador,))
            registros = cursor.fetchall()

    demandas = {}

    for (
        id_alocacao,
        id_demanda,
        nome_demanda,
        inicio,
        termino,
        mes,
        ano,
        percentual
    ) in registros:

        if id_alocacao not in demandas:
            demandas[id_alocacao] = {
                "id_demanda": id_demanda,
                "nome": nome_demanda,
                "inicio": inicio,
                "termino": termino,
                "planejamentos": defaultdict(list),
            }

        mes_numero = converter_mes(mes)

        if mes_numero is None or ano is None:
            continue

        try:
            ano_numero = int(ano)
        except (TypeError, ValueError):
            continue

        if not 1 <= ano_numero <= 9999:
            continue

        chave = (ano_numero, mes_numero)

        demandas[id_alocacao]["planejamentos"][chave].append(
            percentual
        )

    resultado = {}

    for ano, mes in periodo:
        primeiro_dia = date(ano, mes, 1)

        ultimo_dia = date(
            ano,
            mes,
            calendar.monthrange(ano, mes)[1]
        )

        em_vigencia = set()
        com_zero = set()
        sem_planejamento = set()

        for demanda in demandas.values():
            inicio = demanda["inicio"]
            termino = demanda["termino"]

            if not inicio or not termino:
                continue

            vigente = (
                inicio <= ultimo_dia
                and termino >= primeiro_dia
            )

            if not vigente:
                continue

            id_demanda = demanda["id_demanda"]
            em_vigencia.add(id_demanda)

            chave = (ano, mes)

            registros_mes = (
                demanda["planejamentos"].get(chave)
            )

            if not registros_mes:
                sem_planejamento.add(id_demanda)
                continue

            total_planejado = sum(
                valor or 0
                for valor in registros_mes
            )

            if total_planejado == 0:
                com_zero.add(id_demanda)

        resultado[f"{ano}-{mes:02d}"] = {
            "demandas_em_vigencia": len(em_vigencia),
            "demandas_com_zero": len(com_zero),
            "demandas_sem_planejamento": len(
                sem_planejamento
            ),
        }

    return resultado


if __name__ == "__main__":
    periodo_teste = [(2027, 1)]

    contexto = consultar_contexto_alocacoes(
        250,
        periodo_teste
    )

    print("CONTEXTO DAS ALOCACOES")
    print(contexto)
