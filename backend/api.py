
import os
import secrets
import time

from collections import deque
from pathlib import Path
from urllib.parse import parse_qs

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
)
from pydantic import BaseModel, Field
from starlette.middleware.sessions import SessionMiddleware

from interpretador import interpretar_solicitacao
from ranking import classificar_colaboradores
from busca_talentos import buscar_talentos
from contexto_alocacoes import consultar_contexto_alocacoes
from melhoria_ia import melhorar_consulta, ErroOllama


# ============================================================
# CONFIGURACOES
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

load_dotenv(BASE_DIR / ".env")

SENHA_ACESSO = os.getenv("INHIRE_ACCESS_PASSWORD")
CHAVE_SESSAO = os.getenv("INHIRE_SESSION_SECRET")

if not SENHA_ACESSO:
    raise RuntimeError(
        "INHIRE_ACCESS_PASSWORD nao configurada no .env"
    )

if not CHAVE_SESSAO or len(CHAVE_SESSAO) < 32:
    raise RuntimeError(
        "INHIRE_SESSION_SECRET deve ter pelo menos "
        "32 caracteres."
    )


# ============================================================
# APLICACAO FASTAPI
# ============================================================

app = FastAPI(
    title="InHire API",
    description="Motor inteligente de busca de profissionais",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

# ============================================================
# LIMITACAO DE TENTATIVAS DE LOGIN
# ============================================================

MAX_TENTATIVAS = 10
JANELA_TENTATIVAS = 60

tentativas_login = deque()


def limpar_tentativas_antigas():
    agora = time.monotonic()

    while tentativas_login:
        if agora - tentativas_login[0] <= JANELA_TENTATIVAS:
            break

        tentativas_login.popleft()


def login_bloqueado():
    limpar_tentativas_antigas()

    return len(tentativas_login) >= MAX_TENTATIVAS


# ============================================================
# PROTECAO DAS ROTAS
# ============================================================

@app.middleware("http")
async def proteger_aplicacao(request: Request, call_next):

    caminhos_publicos = {
        "/login",
        "/favicon.ico",
    }

    caminho = request.url.path

    if caminho in caminhos_publicos:
        return await call_next(request)

    if not request.session.get("autenticado"):

        if caminho == "/buscar" or request.method != "GET":
            return JSONResponse(
                status_code=401,
                content={
                    "detail": "Acesso nao autorizado."
                },
            )

        return RedirectResponse(
            url="/login",
            status_code=303,
        )

    return await call_next(request)

# ============================================================
# SESSOES
# ============================================================

app.add_middleware(
    SessionMiddleware,
    secret_key=CHAVE_SESSAO,
    session_cookie="inhire_session",
    same_site="lax",
    https_only=True,  # Permite testes locais com HTTP
    max_age=60 * 60 * 8,
)

# ============================================================
# PAGINA DE LOGIN
# ============================================================


LOGIN_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <title>InHire | Acesso Restrito</title>

    <style>
        :root {
            --roxo: #842be3;
            --roxo-hover: #7020c8;
            --violeta: #a175e9;
            --ciano: #00d8e5;
            --escuro: #25143d;
            --lilas: #ede4fa;
            --texto: #2c203e;
            --secundario: #796e87;
        }

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 24px;
            font-family: "Segoe UI", Arial, sans-serif;
            color: var(--texto);

            background:
                radial-gradient(
                    circle at 78% 18%,
                    rgba(0, 216, 229, .22),
                    transparent 35%
                ),
                radial-gradient(
                    circle at 12% 85%,
                    rgba(161, 117, 233, .38),
                    transparent 42%
                ),
                linear-gradient(
                    135deg,
                    #25143d 0%,
                    #572091 55%,
                    #842be3 100%
                );
        }

        .login {
            position: relative;
            z-index: 1;
            width: 100%;
            max-width: 430px;
            background: #ffffff;
            padding: 42px 38px 36px;
            border-radius: 20px;

            box-shadow:
                0 24px 65px rgba(19, 5, 40, .28);

            border: 1px solid rgba(255, 255, 255, .5);
            overflow: hidden;
        }

        .login::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 5px;

            background: linear-gradient(
                90deg,
                var(--roxo),
                var(--violeta),
                var(--ciano)
            );
        }

        .marca {
            text-align: center;
            margin-bottom: 32px;
        }

        .marca-icone {
            display: flex;
            align-items: center;
            justify-content: center;

            width: 56px;
            height: 56px;
            margin: 0 auto 16px;

            border-radius: 16px;
            background: var(--lilas);
            color: var(--roxo);

            font-size: 29px;
            font-weight: 800;
        }

        h1 {
            margin: 0;
            font-size: 35px;
            font-weight: 800;
            letter-spacing: -1.2px;
            color: var(--escuro);
        }

        h1::after {
            content: ".";
            color: var(--ciano);
        }

        .subtitulo {
            margin: 12px auto 0;
            max-width: 290px;
            color: var(--secundario);
            font-size: 13px;
            line-height: 1.7;
        }

        .acesso-label {
            display: inline-block;
            margin-bottom: 9px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--roxo);
        }

        label {
            display: block;
            margin-bottom: 10px;
            font-size: 13px;
            font-weight: 700;
            color: var(--texto);
        }

        .campo {
            position: relative;
        }

        input {
            width: 100%;
            padding: 15px 16px;
            background: #fdfbff;
            border: 1px solid #dccdec;
            border-radius: 10px;
            color: var(--texto);
            outline: none;
            font: inherit;
            font-size: 15px;

            transition:
                border-color .2s,
                box-shadow .2s;
        }

        input::placeholder {
            color: #a59ab1;
        }

        input:focus {
            border-color: var(--roxo);
            box-shadow:
                0 0 0 4px rgba(132, 43, 227, .12);
        }

        .botao-entrar {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;

            width: 100%;
            margin-top: 22px;
            padding: 15px;

            background: var(--roxo);
            color: white;

            border: none;
            border-radius: 10px;

            font: inherit;
            font-size: 14px;
            font-weight: 700;

            cursor: pointer;

            box-shadow:
                0 7px 18px rgba(132, 43, 227, .2);

            transition:
                background .2s,
                transform .2s;
        }

        .botao-entrar:hover {
            background: var(--roxo-hover);
            transform: translateY(-1px);
        }

        .botao-entrar:focus-visible {
            outline: 3px solid var(--ciano);
            outline-offset: 3px;
        }

        .botao-entrar:disabled {
            opacity: .65;
            cursor: wait;
            transform: none;
        }

        .erro {
            display: none;
            color: #b91c1c;
            background: #fef2f2;
            border: 1px solid #fecaca;
            border-radius: 9px;
            padding: 13px;
            margin-bottom: 20px;
            font-size: 13px;
            line-height: 1.5;
        }

        .rodape-login {
            margin-top: 28px;
            padding-top: 20px;
            border-top: 1px solid #eee5f6;
            text-align: center;
        }

        .rodape-login p {
            margin: 0;
            color: #988ba7;
            font-size: 11px;
            line-height: 1.7;
        }

        .rodape-login strong {
            color: var(--roxo);
        }

        @media (max-width: 480px) {
            body {
                padding: 18px;
            }

            .login {
                padding: 36px 25px 29px;
                border-radius: 17px;
            }

            h1 {
                font-size: 31px;
            }

            .marca {
                margin-bottom: 27px;
            }
        }

        @media (prefers-reduced-motion: reduce) {
            *,
            *::before,
            *::after {
                transition: none !important;
            }
        }
    </style>
</head>

<body>

    <main class="login">

        <div class="marca">
            <div class="marca-icone" aria-hidden="true">
                ✦
            </div>

            <h1>InHire</h1>

            <p class="subtitulo">
                Inteligência para conectar talentos
                e oportunidades.
            </p>
        </div>

        <div id="erro" class="erro" role="alert"></div>

        <form method="POST" action="/login">

            <span class="acesso-label">
                Acesso restrito
            </span>

            <label for="senha">
                Senha de acesso
            </label>

            <div class="campo">
                <input
                    id="senha"
                    name="senha"
                    type="password"
                    placeholder="Digite sua senha"
                    autocomplete="current-password"
                    required
                    autofocus
                >
            </div>

            <button
                type="submit"
                class="botao-entrar"
            >
                Entrar na plataforma
                <span aria-hidden="true">→</span>
            </button>

        </form>

        <div class="rodape-login">
            <p>
                <strong>InHire</strong>
                — Busca Inteligente de Profissionais
            </p>

            <p>
                Projeto desenvolvido para o Hackathon
                Vint Global
            </p>
        </div>

    </main>

    <script>
        const parametros = new URLSearchParams(
            window.location.search
        );

        const erro = parametros.get("erro");
        const mensagem = document.getElementById("erro");

        if (erro === "invalida") {
            mensagem.textContent = "Senha incorreta.";
            mensagem.style.display = "block";
        }

        if (erro === "bloqueado") {
            mensagem.textContent =
                "Muitas tentativas. Tente novamente em instantes.";
            mensagem.style.display = "block";
        }

        const formulario = document.querySelector("form");

        formulario.addEventListener("submit", () => {
            const botao = formulario.querySelector("button");
            botao.disabled = true;
            botao.textContent = "Validando acesso...";
        });
    </script>

</body>
</html>
"""


@app.get("/login", response_class=HTMLResponse)
def pagina_login(request: Request):

    if request.session.get("autenticado"):
        return RedirectResponse(
            url="/app",
            status_code=303,
        )

    return HTMLResponse(LOGIN_HTML)


# ============================================================
# AUTENTICACAO
# ============================================================

@app.post("/login")
async def autenticar(request: Request):

    if login_bloqueado():
        return RedirectResponse(
            url="/login?erro=bloqueado",
            status_code=303,
        )

    corpo = await request.body()

    if len(corpo) > 4096:
        raise HTTPException(
            status_code=413,
            detail="Requisicao muito grande.",
        )

    dados = parse_qs(corpo.decode("utf-8"))
    senha = dados.get("senha", [""])[0]

    senha_correta = secrets.compare_digest(
        senha.encode("utf-8"),
        SENHA_ACESSO.encode("utf-8"),
    )

    if not senha_correta:
        tentativas_login.append(time.monotonic())

        return RedirectResponse(
            url="/login?erro=invalida",
            status_code=303,
        )

    tentativas_login.clear()

    request.session.clear()
    request.session["autenticado"] = True

    return RedirectResponse(
        url="/app",
        status_code=303,
    )


# ============================================================
# ENCERRAR SESSAO
# ============================================================

@app.post("/logout")
def sair(request: Request):

    request.session.clear()

    return RedirectResponse(
        url="/login",
        status_code=303,
    )


# ============================================================
# PAGINA PRINCIPAL
# ============================================================

@app.get("/app", include_in_schema=False)
def pagina_web():

    return FileResponse(
        FRONTEND_DIR / "index.html"
    )


# ============================================================
# MODELOS
# ============================================================

class ConsultaRequest(BaseModel):
    texto: str = Field(min_length=1, max_length=1500)


# ============================================================
# ROTA INICIAL
# ============================================================

@app.get("/")
def inicio():

    return RedirectResponse(
        url="/app",
        status_code=303,
    )


# ============================================================
# MELHORIA OPCIONAL DE CONSULTA VIA OLLAMA LOCAL
# ============================================================

@app.post("/melhorar-consulta")
async def melhorar_pesquisa(consulta: ConsultaRequest):
    texto = consulta.texto.strip()
    if not texto:
        raise HTTPException(status_code=400, detail="Digite uma pesquisa para melhorar.")

    try:
        sugestao = await melhorar_consulta(texto)
    except ErroOllama as erro:
        raise HTTPException(status_code=503, detail=str(erro)) from erro

    return {"original": texto, "sugestao": sugestao, "modelo": "qwen3:1.7b"}


# ============================================================
# BUSCA DE PROFISSIONAIS
# ============================================================

@app.post("/buscar")
def buscar_profissionais(consulta: ConsultaRequest):

    try:
        filtros = interpretar_solicitacao(
            consulta.texto
        )

        skills = filtros["skills"]
        periodo = filtros["periodo"]

        percentual = (
            filtros.get("percentual") or 0
        )

        quantidade = filtros.get(
            "quantidade_candidatos", 1
        )

        if not skills or not periodo:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Informe as competencias "
                    "e o periodo da busca."
                ),
            )

        resultados = classificar_colaboradores(
            skills,
            percentual,
            periodo,
            senioridade=filtros.get("senioridade"),
            cargo=filtros.get("cargo"),
        )

        # So consulta o Banco de Talentos se NAO houver nenhum interno elegivel.
        if not resultados:
            talentos = buscar_talentos(
                skills=skills,
                percentual_minimo=percentual,
                cargo=filtros.get("cargo"),
                senioridade=filtros.get("senioridade"),
            )
            return {
                "filtros": filtros,
                "origem_resultado": "talentos",
                "total_encontrado": len(talentos),
                "total_internos": 0,
                "colaboradores": [],
                "talentos": talentos[:quantidade],
            }

        # Enriquece a resposta dos internos sem mudar ranking/disponibilidade.
        selecionados = []
        for colaborador in resultados[:quantidade]:
            contexto = consultar_contexto_alocacoes(colaborador["id"], periodo)
            atualizado = {**colaborador}
            meses_atualizados = []
            for indice, info in enumerate(colaborador["disponibilidade"]):
                mes_atualizado = dict(info)
                if indice < len(periodo):
                    ano, mes = periodo[indice]
                    dados = contexto.get(f"{ano}-{mes:02d}", {})
                    com_zero = dados.get("demandas_com_zero", 0)
                    sem_plano = dados.get("demandas_sem_planejamento", 0)
                    mes_atualizado.update(dados)
                    avisos = []
                    if com_zero:
                        unidade = "demanda" if com_zero == 1 else "demandas"
                        avisos.append(
                            f"{com_zero} {unidade} ainda em vigencia, "
                            "com 0% de alocacao planejada."
                        )
                    if sem_plano:
                        unidade = "demanda" if sem_plano == 1 else "demandas"
                        avisos.append(
                            f"{sem_plano} {unidade} em vigencia sem "
                            "planejamento encontrado para o mes."
                        )
                    mes_atualizado["aviso_vigencia"] = " ".join(avisos)
                meses_atualizados.append(mes_atualizado)
            atualizado["disponibilidade"] = meses_atualizados
            selecionados.append(atualizado)

        return {
            "filtros": filtros,
            "origem_resultado": "internos",
            "total_encontrado": len(resultados),
            "colaboradores": selecionados,
            "talentos": [],
        }

    except HTTPException:
        raise

    except ValueError as erro:
        raise HTTPException(status_code=400, detail=str(erro)) from erro

    except Exception:
        raise HTTPException(
            status_code=500,
            detail=(
                "Erro ao executar a busca "
                "de profissionais."
            ),
        )
