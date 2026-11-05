"""Testes de elegibilidade em todos os meses, sem consultar o PostgreSQL."""
import pytest
import busca


PERIODO = [(2026, 11), (2026, 12), (2027, 1)]


def candidatos():
    return [
        {"id": 1, "nome": "Ana", "senioridade": "Sênior", "cargo": "Desenvolvedor"},
        {"id": 2, "nome": "Bruno", "senioridade": "Pleno", "cargo": "Desenvolvedor"},
    ]


def simular_busca(monkeypatch, disponibilidades, planejamentos=None):
    monkeypatch.setattr(busca, "buscar_por_competencias", lambda skills: candidatos())
    chamadas = []

    def calcular(id_colaborador, ano, mes):
        indice = PERIODO.index((ano, mes))
        chamadas.append((id_colaborador, ano, mes))
        return {
            "ano": ano,
            "mes": mes,
            "disponibilidade": disponibilidades[id_colaborador][indice],
            "possui_planejamento": True if planejamentos is None else planejamentos[id_colaborador][indice],
        }

    monkeypatch.setattr(busca, "calcular_disponibilidade", calcular)
    return chamadas


def test_rejeita_mes_abaixo_de_cinquenta_mesmo_com_media_alta(monkeypatch):
    chamadas = simular_busca(monkeypatch, {1: [80, 80, 80], 2: [100, 20, 100]})
    resultado = busca.buscar_colaboradores(["Node.js", "AWS"], 50, PERIODO)
    assert [c["id"] for c in resultado] == [1]
    assert len(resultado[0]["disponibilidade"]) == 3
    assert (2, 2026, 12) in chamadas
    assert (2, 2027, 1) not in chamadas  # curta-circuito após reprovar


def test_cinquenta_exatos_e_elegivel(monkeypatch):
    simular_busca(monkeypatch, {1: [50, 50, 50], 2: [49, 99, 99]})
    assert [c["id"] for c in busca.buscar_colaboradores(["AWS"], 50, PERIODO)] == [1]


def test_sem_restricao_percentual_permanece_elegivel(monkeypatch):
    simular_busca(monkeypatch, {1: [0, 0, 0], 2: [10, 10, 10]})
    assert len(busca.buscar_colaboradores(["AWS"], 0, PERIODO)) == 2


def test_sem_planejamento_nao_e_confundido_com_planejamento_zero(monkeypatch):
    simular_busca(monkeypatch, {1: [100, 100, 100], 2: [100, 100, 100]},
                 {1: [False, False, False], 2: [True, True, True]})
    resultados = busca.buscar_colaboradores(["AWS"], 50, PERIODO)
    assert len(resultados) == 2  # comportamento atual: ausência de plano não exclui
    assert resultados[0]["disponibilidade"][0]["possui_planejamento"] is False
    assert resultados[1]["disponibilidade"][0]["possui_planejamento"] is True


def test_sem_competencias_nao_retorna_colaboradores(monkeypatch):
    monkeypatch.setattr(busca, "buscar_por_competencias", lambda skills: [])
    monkeypatch.setattr(busca, "calcular_disponibilidade", lambda *args: pytest.fail("Não deveria calcular"))
    assert busca.buscar_colaboradores(["Skill inexistente"], 50, PERIODO) == []
