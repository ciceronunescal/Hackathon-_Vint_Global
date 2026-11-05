# InHire — Plano de Testes

**Projeto:** InHire — Busca Inteligente de Profissionais
**Contexto:** Hackathon Vint Global + INBEC 2026
**Versão do plano:** 1.0
**Data de referência:** 05/11/2026

## 1. Objetivo

Validar que o InHire interpreta solicitações de alocação, identifica profissionais com competências e senioridade compatíveis, verifica a disponibilidade mês a mês e recorre ao Banco de Talentos quando não há colaboradores internos elegíveis. Verificar também a autenticação e o caráter opcional da melhoria de texto com Ollama.

## 2. Escopo

O plano cobre:

- Interpretação de competências, aliases, erros de digitação, cargos, senioridade, percentuais, quantidade de profissionais e períodos.
- Cálculo da disponibilidade mensal, distinção entre planejamento ausente e planejamento registrado com 0% de alocação, e identificação de sobrealocação.
- Elegibilidade por disponibilidade mínima em **cada mês** do período, não pela média.
- Ranking por níveis de competências, disponibilidade mínima, completude do planejamento, experiência, senioridade e critérios de desempate.
- Consulta ao Banco de Talentos, aplicação de filtros e identificação da disponibilidade externa como **declarada e não confirmada mensalmente**.
- Rotas da API, autenticação, controle de acesso, fallback automático e isolamento entre busca principal e serviço de IA.
- Fluxos funcionais realizados manualmente com aplicação e banco em execução.

**Fora do escopo desta rodada:** testes de carga/estresse, análise de segurança ofensiva, cobertura percentual do código, execução de alocação efetiva em projetos e integração em tempo real com um SGD externo.

## 3. Ambiente de referência

- Sistema de validação informado: Windows, PowerShell e Python 3.12.
- Framework de testes: pytest 9.2.0.
- Aplicação: FastAPI + frontend HTML/CSS/JavaScript.
- Dados da aplicação: PostgreSQL 18 em Docker, schema `"InHire"`.
- Assistente de reformulação: Ollama local, opcional.
- Testes automatizados: **mocks/fixtures e dados controlados**, sem escrita no banco real.

## 4. Estratégia e critérios de aceite

| ID | Área | Estratégia | Critério de aprovação |
|---|---|---|---|
| T01 | Interpretador | Testes unitários | Reconhecer requisitos explícitos sem adicionar competências indevidas; respeitar regras de datas e limites |
| T02 | Disponibilidade | Testes unitários com consulta simulada | Calcular `100 − alocação`; informar se há planejamento; sinalizar sobrealocação |
| T03 | Elegibilidade | Testes unitários | Rejeitar candidato quando **qualquer mês** ficar abaixo do mínimo exigido |
| T04 | Ranking | Testes unitários | Aplicar filtros obrigatórios e ordenar conforme os desempates definidos pelo motor |
| T05 | Talentos externos | Testes unitários com dados simulados | Exigir todas as skills, respeitar filtros e não afirmar disponibilidade mensal confirmada |
| T06 | API/autenticação | TestClient/mocks | Negar acesso sem login; preservar login/logout e respostas previstas |
| T07 | Fallback de base | Testes de API com mocks | Consultar talentos apenas quando não existir colaborador interno elegível |
| T08 | IA opcional | Testes de API e fluxo manual | Aceitar reformulação sem interferir no motor de busca; falha da IA não bloquear a busca |
| T09 | Cenário oficial | Teste automatizado e teste manual | Consultar Desenvolvedor Sênior, Node.js, AWS, 50% mensal durante 3 meses |
| T10 | Implantação local | Testes manuais | PostgreSQL saudável, FastAPI inicializado, autenticação e frontend acessíveis |

**Critério de aceite da suíte automatizada:** todos os testes coletados devem passar (`passed`), sem `failed` ou `error`. Avisos devem ser registrados e analisados, mas não são automaticamente falhas.

**Critério de aceite dos testes manuais:** resultado observável coerente com os filtros e comportamento esperado. O registro manual não substitui teste automatizado nem medição de desempenho.

## 5. Inventário da suíte automatizada

| Arquivo | Casos |
|---|---:|
| `tests/test_api.py` | 9 |
| `tests/test_busca.py` | 5 |
| `tests/test_busca_talentos.py` | 11 |
| `tests/test_disponibilidade.py` | 6 |
| `tests/test_interpretador.py` | 19 |
| `tests/test_ranking.py` | 10 |
| **Total** | **60** |

Os nomes e detalhes dos cenários estão nos próprios arquivos `tests/` e no log integral `docs/testes/resultado_pytest.txt`.

## 6. Procedimento de execução

Na **raiz do repositório**, com as dependências instaladas:

```powershell
python -m pytest -v
```

Para gerar novamente a evidência textual:

```powershell
New-Item -ItemType Directory -Path .\docs\testes -Force
python -m pytest -v --tb=short > .\docs\testes\resultado_pytest.txt 2>&1
```

Verificar o resumo:

```powershell
Get-Content .\docs\testes\resultado_pytest.txt | Select-Object -Last 8
```

O arquivo de log deve acompanhar a versão de código à qual se refere; caso o código ou os testes mudem, executar a suíte novamente.

## 7. Procedimentos manuais recomendados

1. Executar `docker compose config --quiet` e `docker compose ps`; verificar PostgreSQL saudável.
2. Iniciar o FastAPI e confirmar a mensagem de startup concluído.
3. Acessar o login local e confirmar a abertura da aplicação após autenticação.
4. Pesquisar: **“Preciso de 1 desenvolvedor sênior com Node.js e AWS, com 50% de disponibilidade a partir de novembro de 2026 por 3 meses.”** Conferir requisitos, período e disponibilidade de cada mês.
5. Pesquisar: **“Quero 1 Analista de Dados com Azure e Docker, com 50% de disponibilidade a partir de 11/2026 por 3 meses.”** Conferir fallback para a base externa e aviso de confirmação da disponibilidade.
6. Solicitar ao Ollama correção de `pythom` e `djago`; aceitar a sugestão e repetir a busca.
7. Realizar uma busca direta sem acionar o botão de IA. Isso confirma o fluxo independente da melhoria de texto, mas **não equivale** a simular indisponibilidade completa do serviço Ollama.

## 8. Riscos, limitações e rastreabilidade

- Um mês sem planejamento registrado pode ter disponibilidade calculada em 100%, **não confirmada**; o usuário deve receber sinalização apropriada.
- A disponibilidade do Banco de Talentos é informada no cadastro e exige confirmação para os meses solicitados.
- Os testes unitários usam simulações e não comprovam, isoladamente, integridade de todos os registros reais do PostgreSQL.
- Os testes executados em 1–2 segundos medem a **suíte automatizada**, não a latência da busca real nem o tempo de inferência do Ollama.
- Não foi medida cobertura de linhas/branches; 100% de testes aprovados não significa 100% de cobertura.
- Evidências: suíte `tests/`, log `docs/testes/resultado_pytest.txt` e relatório `docs/testes/RELATORIO_DE_TESTES.md`.
