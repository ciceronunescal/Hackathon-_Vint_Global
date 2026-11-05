"""Regressao do interpretador de solicitacoes do InHire.

Execute na raiz do projeto: python -m pytest -v tests/test_interpretador.py
Todos os casos usam dados simulados, sem banco e sem Ollama.
"""
from datetime import date

import pytest

from interpretador import interpretar_periodo, interpretar_solicitacao

DATA_BASE = date(2026, 11, 5)


def test_caso_oficial_jose():
    r = interpretar_solicitacao(
        "Preciso de 1 desenvolvedor sênior com Node.js e AWS, "
        "50% de disponibilidade a partir de 11/2026 por 3 meses."
    )
    assert r["cargo"] == "Desenvolvedor"
    assert r["senioridade"] == "Sênior"
    assert set(r["skills"]) == {"Node.js", "AWS (Amazon Web Services)"}
    assert r["percentual"] == 50
    assert r["quantidade_candidatos"] == 1
    assert r["periodo"] == [(2026, 11), (2026, 12), (2027, 1)]
    assert r["origem_periodo"] == "inicio"


def test_tres_meses_padrao_sem_data():
    r = interpretar_solicitacao("Quero um desenvolvedor com Python")
    assert r["periodo"] == [(2026, 11), (2026, 12), (2027, 1)]
    assert r["periodo_padrao"] is True


def test_data_pontual_apenas_um_mes():
    assert interpretar_periodo("disponível em janeiro de 2027", DATA_BASE) == (
        [(2027, 1)], "mes_especifico"
    )


def test_a_partir_de_data_tres_meses():
    assert interpretar_periodo("a partir de janeiro de 2027", DATA_BASE) == (
        [(2027, 1), (2027, 2), (2027, 3)], "inicio"
    )


def test_duracao_seis_meses():
    periodo, origem = interpretar_periodo("a partir de janeiro por 6 meses", DATA_BASE)
    assert periodo == [(2027, m) for m in range(1, 7)]
    assert origem == "inicio"


def test_intervalo_numerico_inclusivo():
    assert interpretar_periodo("de 11/2026 a 02/2027", DATA_BASE) == (
        [(2026, 11), (2026, 12), (2027, 1), (2027, 2)], "intervalo"
    )


def test_intervalo_por_nome():
    assert interpretar_periodo("de janeiro a março de 2027", DATA_BASE) == (
        [(2027, 1), (2027, 2), (2027, 3)], "intervalo"
    )


def test_duracao_sem_data_comeca_no_mes_atual():
    assert interpretar_periodo("durante 2 meses", DATA_BASE) == (
        [(2026, 11), (2026, 12)], "duracao"
    )


def test_mes_sem_ano_resolve_ano_seguinte():
    assert interpretar_periodo("em janeiro", DATA_BASE) == (
        [(2027, 1)], "mes_especifico"
    )


def test_percentual_zero_e_nao_informado():
    assert interpretar_solicitacao("Desenvolvedor com Python 0% disponível")["percentual"] == 0
    assert interpretar_solicitacao("Desenvolvedor com Python")["percentual"] is None


def test_percentual_invalido_rejeitado():
    with pytest.raises(ValueError, match="disponibilidade"):
        interpretar_solicitacao("Desenvolvedor com Python 120% de disponibilidade")


@pytest.mark.parametrize("meses", [0, 121])
def test_duracao_fora_do_limite_rejeitada(meses):
    with pytest.raises(ValueError, match="período"):
        interpretar_periodo(f"por {meses} meses", DATA_BASE)


def test_intervalo_invertido_rejeitado():
    with pytest.raises(ValueError, match="intervalo"):
        interpretar_periodo("de 03/2027 a 01/2027", DATA_BASE)


def test_multiplos_profissionais_e_senioridade():
    r = interpretar_solicitacao(
        "Quero 2 analistas de sistemas juniores com Python a partir de 11/2026 por 3 meses"
    )
    assert r["quantidade_candidatos"] == 2
    assert r["senioridade"] == "Júnior"
    assert r["cargo"] == "Analista de Sistemas"


def test_alias_nodejs():
    r = interpretar_solicitacao("Preciso de desenvolvedor com nodejs e AWS")
    assert "Node.js" in r["skills"]
    assert "AWS (Amazon Web Services)" in r["skills"]


def test_sem_skills_nao_inventa_competencias():
    r = interpretar_solicitacao("Preciso de um desenvolvedor em janeiro")
    assert r["skills"] == []


def test_erros_digitacao_python_django():
    r = interpretar_solicitacao("Preciso de desenvolvedor com pythom e djago em dezembro")
    assert "Python" in r["skills"]
    assert "Django (Python)" in r["skills"]


def test_nodejs_e_javascript_explicitamente_solicitados():
    r = interpretar_solicitacao("Desenvolvedor com Node.js e JS")
    assert "Node.js" in r["skills"]
    assert "JavaScript" in r["skills"]
