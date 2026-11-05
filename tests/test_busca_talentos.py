"""Testes isolados do Banco de Talentos: nenhuma conexao real ao PostgreSQL."""
import importlib.util
import sys
import types
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1] / 'backend'


@pytest.fixture
def mod(monkeypatch):
    banco = types.ModuleType('database')
    banco.get_connection = lambda: None
    psycopg = types.ModuleType('psycopg')
    rows = types.ModuleType('psycopg.rows')
    rows.dict_row = object()
    psycopg.rows = rows
    monkeypatch.setitem(sys.modules, 'database', banco)
    monkeypatch.setitem(sys.modules, 'psycopg', psycopg)
    monkeypatch.setitem(sys.modules, 'psycopg.rows', rows)
    spec = importlib.util.spec_from_file_location('inhire_talentos_testado', BACKEND / 'busca_talentos.py')
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def linha(id, skill, nivel='Avancado', disponibilidade=50, cargo='Analista de Dados', senioridade='Pleno', nome='Talento'):
    return {'id_talento': id, 'nome': nome, 'cargo': cargo, 'senioridade': senioridade,
            'disponibilidade_informada': disponibilidade, 'nome_skill': skill, 'nivel': nivel}


def preparar(monkeypatch, mod, linhas):
    class Cursor:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def execute(self, sql):
            assert '"InHire".talentos' in sql
            assert 't.status IS TRUE' in sql
        def fetchall(self): return linhas
    class Conexao:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def cursor(self, **kwargs): return Cursor()
    monkeypatch.setattr(mod, 'get_connection', lambda: Conexao())


def test_sem_skills_nao_consulta_banco(mod, monkeypatch):
    monkeypatch.setattr(mod, 'get_connection', lambda: (_ for _ in ()).throw(AssertionError('Nao deve consultar')))
    assert mod.buscar_talentos([]) == []


@pytest.mark.parametrize('percentual', [-1, 101])
def test_percentual_invalido_nao_consulta_banco(mod, monkeypatch, percentual):
    monkeypatch.setattr(mod, 'get_connection', lambda: (_ for _ in ()).throw(AssertionError('Nao deve consultar')))
    assert mod.buscar_talentos(['Python'], percentual) == []


def test_exige_todas_as_skills(mod, monkeypatch):
    preparar(monkeypatch, mod, [linha(1,'Python'), linha(2,'Python'), linha(2,'Django')])
    res = mod.buscar_talentos(['Python','Django'], 50)
    assert [t['id'] for t in res] == [2]


def test_normaliza_acentos_e_cargo_senioridade(mod, monkeypatch):
    preparar(monkeypatch, mod, [linha(1,'Python',cargo='Analista de Dados',senioridade='Sênior')])
    res = mod.buscar_talentos(['python'],50,cargo='analista de dados',senioridade='senior')
    assert len(res) == 1


def test_disponibilidade_menor_que_minimo_rejeitada(mod, monkeypatch):
    preparar(monkeypatch, mod, [linha(1,'Python',disponibilidade=49), linha(2,'Python',disponibilidade=50)])
    assert [t['id'] for t in mod.buscar_talentos(['Python'],50)] == [2]


def test_sem_disponibilidade_nao_atende_minimo_positivo(mod, monkeypatch):
    preparar(monkeypatch, mod, [linha(1,'Python',disponibilidade=None), linha(2,'Python',disponibilidade=150)])
    assert mod.buscar_talentos(['Python'],50) == []


def test_disponibilidade_ausente_permitida_sem_minimo_mas_nao_confirmada(mod, monkeypatch):
    preparar(monkeypatch, mod, [linha(1,'Python',disponibilidade=None)])
    res = mod.buscar_talentos(['Python'],0)
    assert len(res) == 1
    assert res[0]['disponibilidade_periodo_confirmada'] is False
    assert res[0]['disponibilidade_informada'] is None


def test_niveis_duplicados_usam_maior(mod, monkeypatch):
    preparar(monkeypatch, mod, [linha(1,'Python','Basico'), linha(1,'Python','Avancado')])
    assert mod.buscar_talentos(['Python'])[0]['niveis'] == {'Python':3}


def test_ranking_prioriza_competencia_antes_da_disponibilidade(mod, monkeypatch):
    preparar(monkeypatch, mod, [linha(1,'Python','Basico',100), linha(2,'Python','Avancado',50)])
    assert [t['id'] for t in mod.buscar_talentos(['Python'],50)] == [2,1]


def test_resultado_nao_contém_pontuacoes_internas(mod, monkeypatch):
    preparar(monkeypatch, mod, [linha(1,'Python')])
    talento = mod.buscar_talentos(['Python'])[0]
    assert talento['origem'] == 'Banco de Talentos'
    assert talento['disponibilidade_periodo_confirmada'] is False
    assert not {'competencia_minima','competencia_total','senioridade_pontos'} & talento.keys()
