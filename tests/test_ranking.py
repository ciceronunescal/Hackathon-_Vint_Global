"""Testes de ranking com candidatos controlados e dependências simuladas."""
import ranking

PERIODO = [(2026, 11), (2026, 12), (2027, 1)]
SKILLS = ["Node.js", "AWS"]


def candidato(identificador, nome, senioridade="Sênior", cargo="Desenvolvedor", livre=(80, 80, 80), planos=(True, True, True)):
    return {
        "id": identificador, "nome": nome, "senioridade": senioridade, "cargo": cargo,
        "disponibilidade": [
            {"disponibilidade": percentual, "possui_planejamento": plano}
            for percentual, plano in zip(livre, planos)
        ],
    }


def executar(monkeypatch, candidatos, niveis, experiencias=None, senioridade=None, cargo=None):
    monkeypatch.setattr(ranking, "buscar_colaboradores", lambda skills, pct, meses: candidatos)
    monkeypatch.setattr(ranking, "consultar_niveis", lambda candidatos, skills: niveis)
    monkeypatch.setattr(ranking, "calcular_experiencia", lambda ident: (experiencias or {}).get(ident, 0))
    return ranking.classificar_colaboradores(SKILLS, 50, PERIODO, senioridade=senioridade, cargo=cargo)


def test_senioridade_e_cargo_sao_filtros_obrigatorios(monkeypatch):
    cs = [candidato(1, "Ana"), candidato(2, "Bruno", senioridade="Pleno"), candidato(3, "Clara", cargo="Analista")]
    niveis = {i: {"NODE.JS": 3, "AWS": 3} for i in (1, 2, 3)}
    resultado = executar(monkeypatch, cs, niveis, senioridade="sênior", cargo="desenvolvedor")
    assert [c["id"] for c in resultado] == [1]


def test_filtro_sem_candidatos_nao_consulta_niveis(monkeypatch):
    monkeypatch.setattr(ranking, "buscar_colaboradores", lambda *args: [])
    monkeypatch.setattr(ranking, "consultar_niveis", lambda *args: (_ for _ in ()).throw(AssertionError("consulta indevida")))
    assert ranking.classificar_colaboradores(SKILLS, 50, PERIODO) == []


def test_prioriza_melhor_competencia_minima(monkeypatch):
    cs = [candidato(1, "Ana"), candidato(2, "Bruno")]
    niveis = {1: {"NODE.JS": 3, "AWS": 1}, 2: {"NODE.JS": 2, "AWS": 2}}
    assert [x["id"] for x in executar(monkeypatch, cs, niveis)] == [2, 1]


def test_desempate_pela_soma_das_competencias(monkeypatch):
    cs = [candidato(1, "Ana"), candidato(2, "Bruno")]
    niveis = {1: {"NODE.JS": 2, "AWS": 2}, 2: {"NODE.JS": 3, "AWS": 2}}
    assert [x["id"] for x in executar(monkeypatch, cs, niveis)] == [2, 1]


def test_desempate_pela_disponibilidade_minima(monkeypatch):
    cs = [candidato(1, "Ana", livre=(90, 50, 90)), candidato(2, "Bruno", livre=(70, 70, 70))]
    niveis = {i: {"NODE.JS": 2, "AWS": 2} for i in (1, 2)}
    assert [x["id"] for x in executar(monkeypatch, cs, niveis)] == [2, 1]


def test_planejamento_registrado_melhora_desempate(monkeypatch):
    cs = [candidato(1, "Ana", planos=(False, False, True)), candidato(2, "Bruno")]
    niveis = {i: {"NODE.JS": 2, "AWS": 2} for i in (1, 2)}
    resultado = executar(monkeypatch, cs, niveis)
    assert [x["id"] for x in resultado] == [2, 1]
    assert resultado[1]["meses_sem_planejamento"] == 2


def test_experiencia_desempata_antes_da_senioridade(monkeypatch):
    cs = [candidato(1, "Ana", senioridade="Sênior"), candidato(2, "Bruno", senioridade="Pleno")]
    niveis = {i: {"NODE.JS": 2, "AWS": 2} for i in (1, 2)}
    assert [x["id"] for x in executar(monkeypatch, cs, niveis, {1: 12, 2: 24})] == [2, 1]


def test_senioridade_desempata_quando_experiencia_igual(monkeypatch):
    cs = [candidato(1, "Ana", senioridade="Pleno"), candidato(2, "Bruno", senioridade="Sênior")]
    niveis = {i: {"NODE.JS": 2, "AWS": 2} for i in (1, 2)}
    assert [x["id"] for x in executar(monkeypatch, cs, niveis)] == [2, 1]


def test_ordem_alfabetica_estavel_no_empate(monkeypatch):
    cs = [candidato(2, "Bruno"), candidato(1, "Ana")]
    niveis = {i: {"NODE.JS": 2, "AWS": 2} for i in (1, 2)}
    assert [x["nome"] for x in executar(monkeypatch, cs, niveis)] == ["Ana", "Bruno"]


def test_niveis_ausentes_nao_sao_inventados(monkeypatch):
    cs = [candidato(1, "Ana")]
    resultado = executar(monkeypatch, cs, {1: {"NODE.JS": 3}})
    assert resultado[0]["niveis"] == {"Node.js": 3, "AWS": 0}
    assert resultado[0]["competencia_minima"] == 0
