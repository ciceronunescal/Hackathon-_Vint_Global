"""Fixtures isoladas: nenhum teste acessa ou altera o PostgreSQL."""
import sys
from datetime import date
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import interpretador


class DataFixa(date):
    @classmethod
    def today(cls):
        return cls(2026, 11, 5)


@pytest.fixture(autouse=True)
def catalogo_simulado(monkeypatch):
    """Congela o relogio e substitui as consultas de catalogos por listas em memoria."""
    monkeypatch.setattr(interpretador, "date", DataFixa)
    monkeypatch.setattr(
        interpretador,
        "carregar_skills",
        lambda: ["Python", "Django (Python)", "Node.js", "AWS (Amazon Web Services)",
                 "Azure", "Docker", "JavaScript", "React", "PostgreSQL"],
    )
    monkeypatch.setattr(
        interpretador,
        "carregar_cargos",
        lambda: ["Desenvolvedor", "Analista de Dados", "Analista de Sistemas"],
    )
