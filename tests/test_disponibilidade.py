"""Testes isolados de disponibilidade: sem conexão real com o banco."""
from datetime import date
from unittest.mock import MagicMock

import pytest
import disponibilidade


def conexao_simulada(monkeypatch, total_alocado, total_planejamentos):
    cursor = MagicMock()
    cursor.fetchone.return_value = (total_alocado, total_planejamentos)
    conn = MagicMock()
    conn.__enter__.return_value = conn
    conn.cursor.return_value.__enter__.return_value = cursor
    monkeypatch.setattr(disponibilidade, "get_connection", lambda: conn)
    return cursor


@pytest.mark.parametrize("alocado,contagem,livre,registrado,sobre", [
    (50, 1, 50, True, False),
    (0, 1, 100, True, False),
    (0, 0, 100, False, False),
    (100, 1, 0, True, False),
    (120, 2, -20, True, True),
])
def test_calculo_mensal_e_sinalizacao(monkeypatch, alocado, contagem, livre, registrado, sobre):
    cursor = conexao_simulada(monkeypatch, alocado, contagem)
    resultado = disponibilidade.calcular_disponibilidade(77, 2027, 1)
    assert resultado["alocacao"] == alocado
    assert resultado["disponibilidade"] == livre
    assert resultado["possui_planejamento"] is registrado
    assert resultado["sobrealocado"] is sobre
    assert resultado["situacao"] == ("COM_PLANEJAMENTO" if registrado else "SEM_PLANEJAMENTO")
    assert resultado["mes"] == "Jan"
    assert resultado["ano"] == 2027
    assert cursor.execute.call_args.args[1] == (77, 2027, "Jan")


def test_proximos_meses_atravessa_ano(monkeypatch):
    class DataFixa:
        @staticmethod
        def today():
            return date(2026, 11, 5)

    monkeypatch.setattr(disponibilidade, "date", DataFixa)
    assert disponibilidade.proximos_meses() == [(2026, 11), (2026, 12), (2027, 1)]
    assert disponibilidade.proximos_meses(1) == [(2026, 11)]
