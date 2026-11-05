"""Testes de API com TestClient e mocks; nao acessam DB ou Ollama."""
import importlib.util
import sys
import types
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND = Path(__file__).resolve().parents[1] / 'backend'


@pytest.fixture
def api(monkeypatch):
    monkeypatch.setenv('INHIRE_ACCESS_PASSWORD', 'senha-teste-123')
    monkeypatch.setenv('INHIRE_SESSION_SECRET', 'chave-ficticia-de-testes-com-mais-de-32-caracteres')
    for nome, atributo in [('interpretador','interpretar_solicitacao'),('ranking','classificar_colaboradores'),
                           ('busca_talentos','buscar_talentos'),('contexto_alocacoes','consultar_contexto_alocacoes')]:
        modulo = types.ModuleType(nome)
        setattr(modulo, atributo, lambda *args, **kwargs: None)
        monkeypatch.setitem(sys.modules, nome, modulo)
    ia = types.ModuleType('melhoria_ia')
    class ErroOllama(Exception): pass
    ia.ErroOllama = ErroOllama
    async def fake_ia(texto): return texto
    ia.melhorar_consulta = fake_ia
    monkeypatch.setitem(sys.modules,'melhoria_ia',ia)
    spec = importlib.util.spec_from_file_location('inhire_api_testada', BACKEND / 'api.py')
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


@pytest.fixture
def client(api):
    # HTTPS assegura persistencia de cookies com Secure=True.
    with TestClient(api.app, base_url='https://testserver') as cliente:
        yield cliente


def autenticado(client):
    resposta = client.post('/login',data={'senha':'senha-teste-123'},follow_redirects=False)
    assert resposta.status_code == 303
    return client


def filtros(**extras):
    base = {'skills':['Node.js','AWS'], 'periodo':[(2026,11),(2026,12),(2027,1)],
            'percentual':50,'quantidade_candidatos':1,'cargo':None,'senioridade':'Sênior'}
    return {**base,**extras}


def test_busca_exige_login(client):
    r = client.post('/buscar',json={'texto':'busca'})
    assert r.status_code == 401


def test_melhorar_exige_login(client):
    assert client.post('/melhorar-consulta',json={'texto':'busca'}).status_code == 401


def test_login_invalido(client):
    assert client.post('/login',data={'senha':'errada'},follow_redirects=False).headers['location'] == '/login?erro=invalida'


def test_busca_interna_nao_chama_talentos(api,client,monkeypatch):
    autenticado(client)
    monkeypatch.setattr(api,'interpretar_solicitacao',lambda texto:filtros())
    monkeypatch.setattr(api,'classificar_colaboradores',lambda *a,**kw:[{'id':1,'nome':'Jose','cargo':'Dev','senioridade':'Sênior','disponibilidade':[{'ano':2026,'mes':'Nov','disponibilidade':80,'possui_planejamento':True}]}])
    monkeypatch.setattr(api,'buscar_talentos',lambda **kw: (_ for _ in ()).throw(AssertionError('Nao pode consultar talentos')))
    monkeypatch.setattr(api,'consultar_contexto_alocacoes',lambda *a:{})
    r = client.post('/buscar',json={'texto':'Node.js AWS'})
    assert r.status_code == 200
    assert r.json()['origem_resultado'] == 'internos'
    assert r.json()['talentos'] == []


def test_fallback_para_talentos_automatico(api,client,monkeypatch):
    autenticado(client)
    monkeypatch.setattr(api,'interpretar_solicitacao',lambda texto:filtros())
    monkeypatch.setattr(api,'classificar_colaboradores',lambda *a,**kw:[])
    chamadas=[]
    def talentos(**kw):
        chamadas.append(kw)
        return [{'id':10,'disponibilidade_periodo_confirmada':False}]
    monkeypatch.setattr(api,'buscar_talentos',talentos)
    r = client.post('/buscar',json={'texto':'Node.js AWS'})
    assert r.status_code == 200
    assert r.json()['origem_resultado'] == 'talentos'
    assert r.json()['talentos'][0]['disponibilidade_periodo_confirmada'] is False
    assert chamadas[0]['percentual_minimo']==50


def test_busca_sem_skills_retorna_400(api,client,monkeypatch):
    autenticado(client)
    monkeypatch.setattr(api,'interpretar_solicitacao',lambda texto:filtros(skills=[]))
    assert client.post('/buscar',json={'texto':'invalido'}).status_code == 400


def test_melhorar_com_ollama(api,client,monkeypatch):
    autenticado(client)
    async def sugerir(texto): return 'Preciso de Python e Django'
    monkeypatch.setattr(api,'melhorar_consulta',sugerir)
    r=client.post('/melhorar-consulta',json={'texto':'pythom e djago'})
    assert r.status_code==200
    assert r.json()['sugestao']=='Preciso de Python e Django'


def test_falha_ollama_nao_afeta_busca(api,client,monkeypatch):
    autenticado(client)
    async def indisponivel(texto): raise api.ErroOllama('IA indisponivel')
    monkeypatch.setattr(api,'melhorar_consulta',indisponivel)
    assert client.post('/melhorar-consulta',json={'texto':'pesquisa'}).status_code==503
    monkeypatch.setattr(api,'interpretar_solicitacao',lambda texto:filtros())
    monkeypatch.setattr(api,'classificar_colaboradores',lambda *a,**kw:[])
    monkeypatch.setattr(api,'buscar_talentos',lambda **kw:[])
    assert client.post('/buscar',json={'texto':'Node.js AWS'}).status_code==200


def test_logout_revoga_acesso(api,client):
    autenticado(client)
    assert client.post('/logout',follow_redirects=False).status_code==303
    assert client.post('/buscar',json={'texto':'busca'}).status_code==401
