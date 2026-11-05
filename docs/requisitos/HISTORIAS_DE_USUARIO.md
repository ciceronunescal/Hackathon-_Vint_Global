# InHire — Histórias de usuário e critérios de aceite

**Projeto:** Hackathon Vint Global + INBEC 2026
**Problema de referência:** “A Busca do José: Como Alocar o Talento Certo na Hora Certa?”
**Ator principal:** José, gerente de projetos
**Escopo:** Busca e recomendação de profissionais para alocação; não executa a efetivação da alocação no SGD.

## 1. Objetivo e contexto

José precisa encontrar rapidamente profissionais com competências técnicas, senioridade e disponibilidade compatíveis com um projeto. A consulta manual ao quadro interno, aos planejamentos mensais e, quando necessário, ao Banco de Talentos gera retrabalho. O InHire concentra a pesquisa em um único fluxo, priorizando colaboradores internos e consultando talentos externos quando nenhum interno satisfaz os filtros.

**Cenário de referência do desafio:** encontrar **1 desenvolvedor sênior** com **Node.js e AWS** e pelo menos **50% de disponibilidade em cada um dos próximos 3 meses**.

## 2. Histórias de usuário

### HU-01 — Descrever a necessidade em linguagem natural

**Como** José, gerente de projetos, **quero** escrever os requisitos em uma única solicitação, **para** localizar profissionais sem preencher filtros técnicos individualmente.

**Critérios de aceite**

- **Dado** um texto com competências cadastradas, **quando** o usuário pesquisar, **então** o sistema identifica as competências exigidas.
- **Dado** um texto com cargo e senioridade reconhecidos, **quando** a busca for processada, **então** esses elementos são utilizados como filtros.
- **Dado** um erro de digitação reconhecido com segurança, **quando** o interpretador processá-lo, **então** mapeia para a competência cadastrada sem acrescentar requisitos não solicitados.
- **Dado** que não seja possível identificar competências, **quando** a busca for enviada, **então** a aplicação não inventa competências e informa que faltam critérios necessários.

**Evidência:** testes do interpretador; teste manual da consulta de Python e Django.

### HU-02 — Definir a janela de alocação

**Como** José, **quero** especificar quando e por quanto tempo preciso do profissional, **para** analisar o período correto.

**Critérios de aceite**

- **Dado** que não informei datas nem duração, **quando** pesquisar, **então** o sistema considera o mês corrente e os 2 meses seguintes e sinaliza que é um período padrão.
- **Dado** “em janeiro de 2027”, **quando** pesquisar, **então** somente janeiro de 2027 é analisado, salvo duração explícita.
- **Dado** “a partir de janeiro de 2027”, **quando** pesquisar, **então** janeiro, fevereiro e março são analisados, salvo duração explícita.
- **Dado** “por 6 meses” com data inicial, **quando** pesquisar, **então** são analisados 6 meses consecutivos.
- **Dado** um intervalo explícito, **quando** pesquisar, **então** o sistema considera os meses inicial e final, inclusive.
- **Dado** um intervalo invertido ou duração fora dos limites aceitos, **quando** interpretar, **então** o sistema rejeita esse período.

**Evidência:** testes automatizados de interpretação de datas e durações.

### HU-03 — Verificar o percentual livre em cada mês

**Como** José, **quero** exigir uma disponibilidade percentual mínima em cada mês, **para** evitar indicar alguém incapaz de atender a toda a duração do projeto.

**Critérios de aceite**

- **Dado** o requisito de 50% por 3 meses, **quando** um colaborador tem 100%, 20% e 100% de disponibilidade, **então** ele não é elegível, independentemente da média.
- **Dado** que o colaborador tem 50% livres em cada mês solicitado, **quando** os filtros são aplicados, **então** ele é elegível nesse critério.
- **Dado** planejamento mensal registrado com 0% de alocação, **quando** a disponibilidade é calculada, **então** o sistema distingue esse registro de um mês sem planejamento.
- **Dado** ausência de planejamento, **quando** a disponibilidade é exibida, **então** ela é identificada como não confirmada, sem ser tratada visualmente como planejamento registrado.

**Evidência:** testes de disponibilidade e busca; cards mensais da aplicação.

**Limitação conhecida:** a regra atual calcula disponibilidade de 100% quando não existe planejamento, mas sinaliza a ausência de confirmação. A validação humana permanece importante antes da alocação.

### HU-04 — Priorizar profissionais internos e classificá-los

**Como** José, **quero** receber uma lista classificada de colaboradores elegíveis, **para** avaliar primeiro as opções internas mais adequadas.

**Critérios de aceite**

- **Dado** que há colaboradores com as competências e disponibilidade exigidas, **quando** a busca termina, **então** são exibidos candidatos internos.
- **Dado** cargo ou senioridade explícitos, **quando** classificar, **então** candidatos incompatíveis com esses filtros são excluídos.
- **Dado** mais de um elegível, **quando** o ranking é calculado, **então** prioriza: nível mínimo das competências, soma dos níveis, disponibilidade mínima, meses com planejamento, experiência, senioridade, disponibilidade média e nome para desempate.
- **Dado** que solicitei apenas 1 profissional, **quando** os resultados são exibidos, **então** a interface apresenta o melhor colocado e indica quantos são elegíveis no total.

**Evidência:** testes de ranking e busca; cenário manual do José.

### HU-05 — Consultar automaticamente o Banco de Talentos

**Como** José, **quero** consultar alternativas externas automaticamente quando não houver colaborador interno elegível, **para** não repetir a pesquisa em outro sistema.

**Critérios de aceite**

- **Dado** que ao menos um colaborador interno é elegível, **quando** a busca é concluída, **então** o Banco de Talentos não é consultado como fallback.
- **Dado** que nenhum colaborador interno atende aos filtros, **quando** a busca termina, **então** o sistema consulta automaticamente a base externa.
- **Dado** um talento externo, **quando** ele for apresentado, **então** deverá possuir todas as competências solicitadas e respeitar cargo, senioridade e percentual informado, quando exigidos.
- **Dado** um talento externo elegível, **quando** seu card é apresentado, **então** sua origem e a necessidade de confirmar disponibilidade no período são informadas.
- **Dado** que não existem resultados em ambas as bases, **quando** a busca termina, **então** a interface apresenta uma mensagem de ausência de candidatos.

**Evidência:** testes automatizados da API e do Banco de Talentos; teste manual de Azure + Docker.

**Limitação conhecida:** a disponibilidade externa é declarada no cadastro; não equivale a planejamento mensal confirmado.

### HU-06 — Entender as recomendações

**Como** José, **quero** visualizar os requisitos aplicados e os detalhes de cada candidato, **para** justificar e conferir a recomendação.

**Critérios de aceite**

- **Dado** uma busca válida, **quando** os resultados são exibidos, **então** a interface mostra período analisado, disponibilidade mínima e duração.
- **Dado** um colaborador interno, **quando** abrir seus resultados, **então** o card exibe cargo, senioridade, competências e disponibilidade mês a mês.
- **Dado** um mês sem planejamento confirmado, **quando** o card é exibido, **então** há aviso visual correspondente.
- **Dado** um talento externo, **quando** exibido, **então** o card diferencia o percentual declarado de uma disponibilidade mensal confirmada.

**Evidência:** validações manuais das telas e dos cards.

### HU-07 — Melhorar opcionalmente a pesquisa com IA local

**Como** José, **quero** receber uma sugestão de reformulação da minha pesquisa, **para** corrigir erros e tornar a solicitação mais clara sem perder controle sobre os requisitos.

**Critérios de aceite**

- **Dado** que clico em “Melhorar minha pesquisa com IA”, **quando** o Ollama responde, **então** recebo uma sugestão para revisar.
- **Dado** uma sugestão, **quando** decido aceitá-la, **então** o texto de pesquisa é atualizado mediante minha confirmação.
- **Dado** que não uso a IA, **quando** clico diretamente em Buscar, **então** a busca tradicional funciona.
- **Dado** falha no serviço de IA, **quando** a melhoria não pode ser concluída, **então** o mecanismo normal de busca permanece disponível.

**Evidência:** teste manual de sugestão aceita; testes automatizados da API com simulação de sucesso e falha do Ollama.

### HU-08 — Restringir o acesso ao sistema

**Como** responsável pelo InHire, **quero** exigir autenticação, **para** evitar acesso não autorizado às informações da aplicação.

**Critérios de aceite**

- **Dado** um usuário não autenticado, **quando** acessa as rotas protegidas, **então** a aplicação bloqueia o acesso.
- **Dado** uma senha inválida, **quando** tenta entrar, **então** o login é recusado.
- **Dado** uma sessão válida, **quando** o usuário faz logout, **então** as rotas protegidas deixam de estar disponíveis nessa sessão.

**Evidência:** testes automatizados da API e teste manual de login local.

## 3. Rastreabilidade com o desafio

| Necessidade do desafio | História relacionada | Evidência principal |
|---|---|---|
| Busca por Node.js + AWS e senioridade | HU-01, HU-04 | Teste do caso oficial do José |
| Disponibilidade mensal de 50% por 3 meses | HU-02, HU-03 | Testes de período, disponibilidade e busca |
| Reduzir consultas manuais e retrabalho | HU-01, HU-04, HU-06 | Fluxo demonstrado na interface |
| Consultar duas bases no mesmo fluxo | HU-05 | Teste do fallback automático |
| Experiência intuitiva | HU-06, HU-07 | Testes manuais da interface e IA opcional |
| Uso restrito | HU-08 | Testes da API e autenticação |

## 4. Situação das validações

- **Testes automatizados:** 60 testes aprovados, 0 falhas, 1 aviso de depreciação, execução de referência de 1,09 s, conforme `docs/testes/resultado_pytest.txt` gerado no ambiente Windows do projeto.
- **Testes manuais:** inicialização do Docker/PostgreSQL e FastAPI, login, caso oficial do José, fallback para o Banco de Talentos e sugestão opcional do Ollama foram validados durante a preparação da entrega.
- **Não comprovado:** tempo fim a fim inferior a 5 minutos em medição formal; cobertura percentual de linhas/branches; execução em outro computador; integração em tempo real com o SGD; confirmação mensal da disponibilidade dos talentos externos.

**Referências internas do repositório:** `tests/`, `docs/testes/PLANO_DE_TESTES.md`, `docs/testes/RELATORIO_DE_TESTES.md` e `docs/testes/resultado_pytest.txt`.
