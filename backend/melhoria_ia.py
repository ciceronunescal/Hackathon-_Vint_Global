"""Melhoria opcional de consultas usando Ollama local. Não altera busca/ranking."""

import asyncio
import json
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "qwen3:1.7b"
TIMEOUT_SEGUNDOS = 27


class ErroOllama(Exception):
    """Falha segura: usuário pode pesquisar sem IA."""


def _marcadores(texto):
    """Preserva literalmente números, percentuais e datas da consulta."""
    return sorted(item.strip() for item in re.findall(r"\d+(?:[.,/]\d+)*\s*%?", texto))


def _solicitar_ollama(texto):
    instrucoes = (
        "Você é um revisor de consultas para um sistema de busca de profissionais. "
        "Corrija ortografia, nomes de tecnologias e clareza da frase. "
        "NÃO responda à solicitação, NÃO afirme existir profissional disponível, "
        "NÃO acrescente nem elimine requisitos. Preserve cargo, habilidades, "
        "senioridade, quantidades, datas, período e disponibilidade. "
        "Não deduza ano ou mês ausente. Não substitua tecnologias por outras. "
        "Responda SOMENTE com a consulta revisada em uma única frase, "
        "sem explicações, aspas, saudações ou markdown."
    )
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": f"{instrucoes}\n\nConsulta original: {texto}\n\nConsulta revisada:",
        "stream": False,
        "think": False,
        "options": {"temperature": 0, "num_predict": 125, "num_ctx": 1024},
        "keep_alive": "5m",
    }
    req = Request(
        OLLAMA_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=TIMEOUT_SEGUNDOS) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (TimeoutError, URLError, HTTPError, OSError, ValueError) as exc:
        raise ErroOllama(
            "A IA local não respondeu a tempo ou está indisponível. "
            "Você pode buscar profissionais normalmente."
        ) from exc

    sugestao = str(result.get("response") or "").strip().strip('"“”')
    # Rejeita texto evidentemente fora do formato e alterações numéricas.
    if (not sugestao or len(sugestao) > 2000 or len(sugestao) > max(220, len(texto) * 2.5)
            or "\n" in sugestao or _marcadores(sugestao) != _marcadores(texto)):
        raise ErroOllama(
            "A IA não gerou uma reformulação confiável. "
            "Revise sua pesquisa ou utilize a busca normal."
        )
    return sugestao


async def melhorar_consulta(texto):
    return await asyncio.to_thread(_solicitar_ollama, texto)
