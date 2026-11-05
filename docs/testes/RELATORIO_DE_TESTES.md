# InHire — Relatório de Execução e Validação de Testes

**Projeto:** InHire — Busca Inteligente de Profissionais
**Contexto:** Hackathon Vint Global + INBEC 2026
**Data da execução registrada:** 05/11/2026
**Ambiente informado:** Windows, Python 3.12, pytest 9.2.0
**Fonte da evidência:** saída do pytest fornecida pelo responsável pela execução, registrada em `resultado_pytest.txt`.

## 1. Resultado executivo

| Indicador | Resultado |
|---|---:|
| Testes automatizados coletados | **60** |
| Aprovados | **60** |
| Falhas | **0** |
| Erros reportados | **0** |
| Avisos | **1** |
| Tempo total da execução registrada | **1,09 segundo** |
| Taxa de aprovação dos casos executados | **100%** |

**Conclusão da suíte:** APROVADA para os **60 cenários executados**. Essa taxa de aprovação não representa cobertura integral do código nem prova ausência de defeitos não contemplados pelos casos.

## 2. Resultado detalhado por módulo

| Módulo | Arquivo | Testes | Situação |
|---|---|---:|---|
| API e autenticação | `tests/test_api.py` | 9 | Aprovado |
| Busca interna | `tests/test_busca.py` | 5 | Aprovado |
| Banco de Talentos | `tests/test_busca_talentos.py` | 11 | Aprovado |
| Disponibilidade | `tests/test_disponibilidade.py` | 6 | Aprovado |
| Interpretação de solicitações | `tests/test_interpretador.py` | 19 | Aprovado |
| Ranking | `tests/test_ranking.py` | 10 | Aprovado |
| **Total** | | **60** | **Aprovado** |

### Comportamentos relevantes validados

- **Caso do José:** reconhecimento de Node.js + AWS, senioridade e requisitos de período e disponibilidade.
- **Correção de competência:** o interpretador corrigido evita que `Node.js` adicione indevidamente `JavaScript` como skill independente; continua aceitando `JavaScript` quando solicitado explicitamente.
- **Datas e duração:** diferença entre mês pontual, `a partir de`, intervalo fechado, mês sem ano e duração padrão.
- **Disponibilidade:** limite mensal, planejamento registrado com 0% de alocação, ausência de planejamento, sobrealocação e rejeição de mês abaixo do mínimo.
- **Ranking:** prioridade da competência mínima e soma dos níveis, desempates de disponibilidade, planejamento, experiência e senioridade.
- **Banco de Talentos:** todas as skills exigidas, filtros de cargo/senioridade, disponibilidade declarada e ausência de confirmação mensal.
- **API:** autenticação, controle de acesso, fallback automático para talentos e tratamento da falha de IA sem impedir busca tradicional.

## 3. Validações manuais realizadas

As verificações abaixo foram relatadas e ilustradas por saídas do terminal e capturas da interface. São evidências **funcionais manuais**, distintas dos testes unitários com mocks.

| ID | Verificação | Evidência observada | Resultado |
|---|---|---|---|
| M01 | Serviços Docker | PostgreSQL 18 `healthy`; pgAdmin `Up` | Aprovado |
| M02 | Verificação das dependências | `python -m pip check`: `No broken requirements found.` | Aprovado |
| M03 | Inicialização do backend | Uvicorn: `Application startup complete.` | Aprovado |
| M04 | Login local | Usuário autenticou e abriu a aplicação principal | Aprovado |
| M05 | Cenário oficial Node.js + AWS | Colaborador interno Sênior elegível; 100% de disponibilidade planejada em nov/2026, dez/2026 e jan/2027; mínimo solicitado de 50% | Aprovado |
| M06 | Fallback para Banco de Talentos | Sem interno elegível, foi exibida alternativa externa com Azure, Docker e 50% de disponibilidade **declarada**, acompanhada de aviso de confirmação | Aprovado |
| M07 | Melhoria opcional com IA | Sugestão do Ollama apresentada e aceita pelo usuário; pesquisa realizada depois | Aprovado |
| M08 | Busca direta sem utilizar IA | Resultado da busca principal exibido sem acionar melhoria de texto | Aprovado |

O cenário M08 demonstra que a busca direta não exige acionar a IA. **Não foi executado teste manual de falha completa do processo/serviço Ollama.** O cenário de falha da IA está coberto por teste automatizado da API com simulação.

## 4. Aviso registrado

A execução apresentou **1 aviso**, sem falha de teste:

```text
StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
```

Trata-se de aviso de compatibilidade/depreciação na camada de testes, não de falha observada na busca. Recomenda-se avaliar a atualização em ciclo posterior, com nova execução integral da suíte.

## 5. Não conformidade identificada e tratada

Durante a preparação dos testes do interpretador, foi identificado que o alias `js` podia ser reconhecido dentro de `Node.js`, adicionando `JavaScript` como requisito não solicitado. O código do interpretador foi corrigido e os testes foram posteriormente executados no ambiente do responsável, com **19/19 casos do interpretador aprovados** e **60/60 casos totais aprovados**.

A primeira falha foi relatada na preparação dos testes, mas o usuário substituiu o interpretador **antes** de executar a suíte inicial no Windows. Portanto, o presente relatório **não apresenta uma execução local anterior à correção**; registra apenas o resultado final aprovado no Windows.

## 6. Limitações e recomendações

1. **Cobertura:** não foi executado `pytest-cov` ou medição de linhas/branches; não afirmar 100% de cobertura.
2. **Banco real:** testes automatizados priorizaram mocks; as consultas reais foram exercitadas por fluxos manuais, sem auditoria exaustiva da base.
3. **Performance:** 1,09 segundo é o tempo da suíte de testes, **não** o tempo de resposta do InHire diante de uma consulta real. O requisito de decisão em menos de cinco minutos não foi cronometrado formalmente.
4. **Ollama:** pode ser mais lento em máquinas sem GPU dedicada; recurso opcional, não integrante do cálculo determinístico do ranking.
5. **Planejamentos ausentes:** disponibilidade calculada não equivale a disponibilidade confirmada; a interface diferencia os estados.
6. **Talentos externos:** percentual de disponibilidade é declarado e requer confirmação antes da alocação.
7. **Reprodução:** antes da entrega, manter `tests/`, `docs/testes/resultado_pytest.txt`, dependências, instruções de execução e base autorizada para testes na mesma versão do código.

## 7. Comando e evidência

Comando utilizado para gerar o arquivo de evidências:

```powershell
python -m pytest -v --tb=short > .\docs\testes\resultado_pytest.txt 2>&1
```

Resumo final registrado:

```text
======================== 60 passed, 1 warning in 1.09s ========================
```

Para reproduzir:

```powershell
python -m pytest -v
```

**Resultado geral:** os requisitos testados do motor de interpretação, disponibilidade, elegibilidade, ranking, seleção de talentos e rotas da API foram atendidos nos cenários automatizados executados. Os fluxos manuais essenciais também apresentaram os comportamentos esperados nas verificações realizadas.
