"""Busca alternativa no Banco de Talentos do InHire.

Nao usa os planejamentos dos colaboradores internos: a disponibilidade
externa e o percentual informado no cadastro, sem confirmacao por periodo.
"""

import unicodedata
from collections import defaultdict

from psycopg.rows import dict_row

from database import get_connection


NIVEIS = {"BASICO": 1, "INTERMEDIARIO": 2, "AVANCADO": 3}
SENIORIDADES = {"TRAINEE": 1, "JUNIOR": 2, "PLENO": 3, "SENIOR": 4}


def normalizar(valor):
    texto = unicodedata.normalize("NFKD", str(valor or ""))
    return "".join(c for c in texto if not unicodedata.combining(c)).strip().upper()


def buscar_talentos(skills, percentual_minimo=0, cargo=None, senioridade=None):
    """Retorna talentos ativos com TODAS as competencias exigidas.

    Os filtros de cargo/senioridade sao exatos apos normalizacao.
    A disponibilidade informada e um dado de cadastro, nao uma garantia
    para cada mes do periodo solicitado.
    """
    if not skills:
        return []

    requeridas = {normalizar(nome) for nome in skills if normalizar(nome)}
    percentual_minimo = int(percentual_minimo or 0)

    if not requeridas or not 0 <= percentual_minimo <= 100:
        return []

    sql = """
        SELECT
            t.id AS id_talento,
            t.nome_abreviado AS nome,
            cargo.valor_dominio AS cargo,
            senioridade.valor_dominio AS senioridade,
            t.disponibilidade_informada_percentual AS disponibilidade_informada,
            s.nome_skill,
            nivel.valor_dominio AS nivel
        FROM "InHire".talentos t
        LEFT JOIN "InHire".dominios cargo ON cargo.id = t.id_cargo
        LEFT JOIN "InHire".dominios senioridade ON senioridade.id = t.id_senioridade
        JOIN "InHire".talento_skills ts ON ts.id_talento = t.id
        JOIN "InHire".skills s ON s.id = ts.id_skill
        LEFT JOIN "InHire".dominios nivel ON nivel.id = ts.id_nivel_conhecimento
        WHERE t.status IS TRUE
          AND s.status IS TRUE
          AND s.deletado IS DISTINCT FROM TRUE
    """

    with get_connection() as conexao:
        with conexao.cursor(row_factory=dict_row) as cursor:
            cursor.execute(sql)
            registros = cursor.fetchall()

    agrupados = {}
    for registro in registros:
        id_talento = registro["id_talento"]
        if id_talento not in agrupados:
            agrupados[id_talento] = {
                "id": id_talento,
                "nome": registro["nome"],
                "cargo": registro["cargo"],
                "senioridade": registro["senioridade"],
                "disponibilidade_informada": registro["disponibilidade_informada"],
                "competencias_por_nome": defaultdict(int),
            }
        nome = normalizar(registro["nome_skill"])
        if nome in requeridas:
            nivel = NIVEIS.get(normalizar(registro["nivel"]), 0)
            competencias = agrupados[id_talento]["competencias_por_nome"]
            competencias[nome] = max(competencias[nome], nivel)

    resultado = []
    for talento in agrupados.values():
        competencias = talento.pop("competencias_por_nome")
        if not requeridas.issubset(competencias):
            continue
        if cargo and normalizar(talento["cargo"]) != normalizar(cargo):
            continue
        if senioridade and normalizar(talento["senioridade"]) != normalizar(senioridade):
            continue

        disponibilidade = talento["disponibilidade_informada"]
        if disponibilidade is None or not 0 <= disponibilidade <= 100:
            # Sem percentual valido nao e possivel comprovar o minimo solicitado.
            if percentual_minimo > 0:
                continue
        elif disponibilidade < percentual_minimo:
            continue

        pontos = [competencias[normalizar(skill)] for skill in skills]
        talento.update({
            "origem": "Banco de Talentos",
            "niveis": {skill: competencias[normalizar(skill)] for skill in skills},
            "competencia_minima": min(pontos),
            "competencia_total": sum(pontos),
            "senioridade_pontos": SENIORIDADES.get(normalizar(talento["senioridade"]), 0),
            "disponibilidade_periodo_confirmada": False,
        })
        resultado.append(talento)

    resultado.sort(key=lambda t: (
        -t["competencia_minima"],
        -t["competencia_total"],
        -(t["disponibilidade_informada"] if t["disponibilidade_informada"] is not None else -1),
        -t["senioridade_pontos"],
        normalizar(t["nome"]),
        t["id"],
    ))
    for talento in resultado:
        talento.pop("competencia_minima", None)
        talento.pop("competencia_total", None)
        talento.pop("senioridade_pontos", None)
    return resultado
