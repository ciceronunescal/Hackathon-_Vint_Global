# InHire — Busca Inteligente de Profissionais

**Projeto para o Hackathon Vint Global / INBEC 2026**

O InHire ajuda gestores a encontrar profissionais de tecnologia compatíveis com uma necessidade de projeto, considerando **competências, senioridade e disponibilidade percentual em cada mês**. A solução prioriza colaboradores internos e, se não houver nenhum elegível, procura automaticamente alternativas no Banco de Talentos.

## 1. O desafio

No cenário proposto, José, gerente de projetos, precisa encontrar **1 desenvolvedor sênior com Node.js e AWS e pelo menos 50% de disponibilidade mensal nos próximos três meses**. A verificação manual das competências e da capacidade disponível em diversos projetos, além da consulta separada a candidatos externos, torna a decisão lenta.

O InHire reúne essas verificações em uma pesquisa em linguagem natural, permitindo inspecionar os candidatos e os critérios aplicados.

## 2. Funcionalidades

- Pesquisa em português por cargo, competências técnicas, senioridade, quantidade de profissionais, percentual mínimo de disponibilidade e período.
- Interpretação de expressões temporais: mês específico, início em determinada data, duração explícita e intervalos; quando não há referência temporal, utiliza horizonte padrão de três meses; um mês específico sem duração explícita é tratado como consulta pontual.
- Cálculo e filtragem por **disponibilidade mínima em cada mês** do período, sem substituir essa regra por média mensal.
- Classificação de profissionais internos conforme os critérios interpretados, habilidades e histórico de experiência.
- Indicação dos meses com planejamento registrado e alertas sobre demandas vigentes sem planejamento ou com alocação planejada de 0%.
- Fallback automático para **Banco de Talentos** somente quando não há colaborador interno elegível. A disponibilidade externa é **declarada** e precisa de confirmação para o período.
- Melhoria opcional do texto da pesquisa com um modelo local via Ollama: a sugestão depende de aceite do usuário; **a IA não define os resultados da busca**.
- Interface web responsiva e acesso protegido por sessão e senha.

**Limite do escopo:** a ferramenta recomenda profissionais elegíveis; não efetua uma alocação contratual ou atualização automática no SGD. O banco PostgreSQL utilizado é a base disponibilizada para o desafio, não uma integração em tempo real com o SGD.

## 3. Arquitetura e tecnologias

| Camada | Tecnologia / responsabilidade |
| --- | --- |
| Interface | HTML, CSS e JavaScript (`frontend/index.html`) |
| API e autenticação | Python, FastAPI, Uvicorn, sessões assinadas (`backend/api.py`) |
| Interpretação | Regras determinísticas (`backend/interpretador.py`) |
| Busca e ranking | Módulos Python (`backend/ranking.py`, `backend/busca_talentos.py` e auxiliares) |
| Persistência | PostgreSQL 18, schema `"InHire"`, conexão via `psycopg` |
| Execução do banco | Docker Compose; pgAdmin opcional |
| IA de apoio (opcional) | Ollama local, testado com `qwen3:1.7b` |

O código da API utiliza `backend/database.py` para conectar ao PostgreSQL. Se `DATABASE_URL` estiver preenchida, ela tem precedência; caso contrário, usa `localhost:5432`, banco e usuário `hackathon`, e a senha de `POSTGRES_PASSWORD`.

## 4. Pré-requisitos

- Python 3.12 (ambiente utilizado na validação) e dependências de `requirements.txt`.
- Docker e Docker Compose para iniciar o PostgreSQL 18, ou uma instância PostgreSQL 18 acessível.
- **Arquivo de banco fornecido separadamente** pelo responsável pela entrega.
- Opcional: Ollama e o modelo `qwen3:1.7b` para o botão de melhoria de texto.

## 5. Configuração inicial

### 5.1. Obter o projeto e criar o ambiente Python

No terminal PowerShell, dentro da pasta do repositório:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

No Linux/macOS, ative o ambiente com `source .venv/bin/activate`.

### 5.2. Variáveis de ambiente

Copie `.env.example` para `.env` e substitua os valores de exemplo por **valores próprios do avaliador**:

```powershell
Copy-Item .env.example .env
```

Variáveis obrigatórias para a aplicação: `INHIRE_ACCESS_PASSWORD` e `INHIRE_SESSION_SECRET` (mínimo de 32 caracteres). Para o banco, configure `POSTGRES_PASSWORD` e, se necessário, `DATABASE_URL`.

#### Acesso dos avaliadores: como definir a senha do InHire

**A banca não precisa receber nem conhecer a senha utilizada pelo desenvolvedor.** O próprio avaliador define a senha de login no seu arquivo `.env` local, antes de iniciar a API. Por exemplo:

```dotenv
# Senha do PostgreSQL: defina a mesma senha para o Docker Compose e o backend.
POSTGRES_PASSWORD=substitua_por_uma_senha_local_do_banco

# Se o PostgreSQL estiver em localhost:5432, esta variável pode ficar vazia.
DATABASE_URL=

# Senha que o avaliador utilizará na TELA DE LOGIN do InHire.
INHIRE_ACCESS_PASSWORD=escolha_uma_senha_para_acessar_o_inhire

# Chave interna para assinar sessões; NÃO é a senha de login.
INHIRE_SESSION_SECRET=substitua_por_uma_chave_aleatoria_longa_e_unica
```

Para gerar uma chave de sessão aleatória no PowerShell, use:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Copie o resultado para `INHIRE_SESSION_SECRET` no `.env`. Após iniciar o servidor, acesse `http://127.0.0.1:8000/login` e entre com **o valor que você mesmo definiu em `INHIRE_ACCESS_PASSWORD`**. A aplicação não utiliza cadastro de usuário nem exige credenciais do autor do projeto. **A senha do PostgreSQL é diferente da senha de acesso à interface**, mesmo que ambas estejam no mesmo `.env`.

**Segurança:** nunca publique `.env` no GitHub nem reutilize o token pessoal disponibilizado no evento. O arquivo `.env.example` deve conter apenas valores fictícios. Não envie a chave de sessão ou a senha de acesso real à banca; os avaliadores as criam no próprio ambiente.

### 5.3. Restaurar os dados do desafio

O Compose monta `./db` no diretório de inicialização do PostgreSQL. **O diretório `db/` e os dados reais não acompanham o repositório**: serão fornecidos separadamente. Coloque o script SQL de inicialização recebido dentro de `db/` **antes da primeira criação do volume**.

Em seguida:

```powershell
docker compose up -d
docker compose ps
```

Confirme que `hackathon-postgres` está `healthy`. Um script `.sql` de inicialização será executado apenas quando o diretório de dados estiver vazio. **Não use `docker compose down -v` em um ambiente com dados que precise preservar:** esse comando remove os volumes e apaga o banco local.

Se a base for entregue em formato de **backup customizado** (`.backup`/`.dump`) e não SQL de inicialização, a restauração exige `pg_restore` em vez de simplesmente copiar o arquivo para `db/`. Nesse caso, utilize as instruções que acompanham o backup.

### 5.4. Iniciar a aplicação

A partir da pasta `backend`:

```powershell
cd backend
python -m uvicorn api:app --host 127.0.0.1 --port 8000
```

A aplicação atende em `http://127.0.0.1:8000/login`; após a autenticação, abre `/app`.

**Sessão e HTTPS:** o projeto usa cookie de sessão com a opção `https_only=True`. No computador de desenvolvimento, o login foi testado com sucesso em `http://127.0.0.1:8000/login`; isso não garante que funcionará da mesma maneira em todos os navegadores/endereços HTTP. Para acesso remoto, utilize HTTPS. Se o navegador do avaliador não persistir a sessão no acesso local, verifique a política de cookies e a configuração da sessão antes de alterar qualquer parâmetro de segurança; nunca exponha uma versão com cookies inseguros à internet.

### 5.5. pgAdmin (opcional)

O Compose de distribuição expõe o pgAdmin em `http://localhost:5050` e **não deve depender** de um arquivo local `pgadmin/servers.json`. Antes de executar, confira que o `docker-compose.yaml` usado é a versão preparada para distribuição; o arquivo original do evento fazia essa montagem. Se necessário, cadastre o servidor manualmente no pgAdmin com host `postgres` (dentro da rede Docker), porta `5432`, banco `hackathon`, usuário `hackathon` e a senha definida em `POSTGRES_PASSWORD`.

## 6. Ollama (opcional)

O mecanismo principal de busca **não depende de IA generativa**. Para habilitar a sugestão de reformulação de texto, instale o Ollama e baixe o modelo testado:

```powershell
ollama pull qwen3:1.7b
```

Mantenha o serviço local do Ollama ativo. Se estiver indisponível ou lento, a pesquisa convencional permanece utilizável. O desempenho depende do hardware.

## 7. Roteiro de validação funcional

A demonstração deve utilizar dados presentes no banco restaurado. Os resultados específicos **dependem dos registros e dos planejamentos efetivamente disponíveis**.

| Cenário | Entrada de exemplo | Resultado a verificar |
| --- | --- | --- |
| Caso oficial | `Quero 1 desenvolvedor sênior com Node.js e AWS e 50% de disponibilidade pelos próximos 3 meses` | Aplicação de senioridade, duas skills e 50% em **todos** os meses |
| Mês específico | `Preciso de um dev Python em janeiro de 2027` | Período somente de janeiro/2027 |
| Início sem duração | `Preciso de um dev Python a partir de janeiro de 2027` | Janeiro, fevereiro e março/2027 |
| Duração explícita | `Preciso de um dev Python a partir de janeiro de 2027 por 6 meses` | Janeiro a junho/2027 |
| Busca externa | Consulta sem colaborador interno elegível, mas com talento externo compatível | Consulta automática ao Banco de Talentos, com aviso de disponibilidade declarada |
| Melhoria de texto | `preciso de um dev com pythom e djago` | Sugestão corrigida pela IA, **sem busca automática e sem alterar os critérios sem aceite** |

A interface distingue colaboradores internos e candidatos externos; disponibilidade externa exige confirmação humana. Os testes manuais do ambiente de desenvolvimento validaram login, busca interna, fallback para talentos e melhoria opcional via Ollama. Tempos de resposta do cruzamento com o banco real não foram aferidos de forma controlada.

## 8. Testes automatizados e evidências

Foram executados **60 cenários automatizados**, todos aprovados, em Windows com Python 3.12. A última execução registrada terminou em **1,09 s**, com **1 aviso de depreciação** relacionado ao `starlette.testclient` / `httpx` e **0 falhas**. Os testes usam dados simulados e mocks para não modificar o PostgreSQL; por isso, o tempo de 1,09 s **não representa a latência real da busca no banco** e a aprovação dos testes **não equivale a cobertura de código de 100%**.

Para instalar as dependências de teste e executar a suíte na raiz do projeto:

```powershell
python -m pip install pytest httpx
python -m pytest -v
```

Documentação e evidências:

- [Histórias de usuário e critérios de aceite](docs/requisitos/HISTORIAS_DE_USUARIO.md)
- [Plano de testes](docs/testes/PLANO_DE_TESTES.md)
- [Relatório de testes](docs/testes/RELATORIO_DE_TESTES.md)
- [Saída real do pytest](docs/testes/resultado_pytest.txt)

A suíte cobre interpretação de solicitações, períodos, disponibilidade, elegibilidade, ranking, autenticação da API, fallback para o Banco de Talentos e integração opcional com Ollama por meio de mocks. Os testes manuais complementam essa suíte com a aplicação e o banco reais.

## 9. Organização do projeto

```text
hackathon-vintglobal/
├── backend/
│   ├── api.py                  # Rotas, autenticação e orquestração da busca
│   ├── database.py             # Conexão com PostgreSQL
│   ├── interpretador.py        # Interpretação de filtros e períodos
│   ├── busca.py                # Elegibilidade mensal
│   ├── disponibilidade.py      # Cálculo de disponibilidade
│   ├── ranking.py              # Classificação dos colaboradores
│   ├── busca_talentos.py       # Alternativas externas
│   ├── contexto_alocacoes.py   # Alertas de vigência/planejamento
│   └── melhoria_ia.py          # Sugestão opcional com Ollama
├── frontend/
│   └── index.html
├── tests/
│   ├── test_api.py
│   ├── test_busca.py
│   ├── test_busca_talentos.py
│   ├── test_disponibilidade.py
│   ├── test_interpretador.py
│   └── test_ranking.py
├── docs/
│   ├── requisitos/HISTORIAS_DE_USUARIO.md
│   └── testes/
│       ├── PLANO_DE_TESTES.md
│       ├── RELATORIO_DE_TESTES.md
│       └── resultado_pytest.txt
├── docker-compose.yaml
├── requirements.txt
├── .env.example
└── README.md
```

A pasta `db/` e os dados do desafio são entregues separadamente. Arquivos de exportação, logs, credenciais locais e scripts auxiliares que não são necessários à execução não integram a entrega. O arquivo `iniciar_inhire.bat`, se incluído, é uma conveniência para execução no Windows; o servidor também pode ser iniciado pelo comando Uvicorn informado acima.

## 10. Escopo, segurança e responsabilidade de uso

O InHire **recomenda** profissionais com base nas informações disponibilizadas, mas não executa alocações ou contratações. A disponibilidade mensal calculada depende da qualidade e completude dos planejamentos cadastrados. Na ausência de planejamento, a interface sinaliza que a disponibilidade não foi confirmada; para candidatos externos, o percentual é informado pelo cadastro e requer validação humana para o período solicitado.

O banco de dados utilizado no desafio será entregue separadamente e deve ser tratado conforme as regras da organização e as autorizações de compartilhamento. Não publique senhas, tokens, `.env`, informações pessoais desnecessárias nem exportações de colaboradores no repositório.

**Nota de reprodutibilidade:** a aplicação e os testes foram validados no ambiente de desenvolvimento. A instalação em outro computador deve ser conferida após restaurar a base fornecida e configurar as variáveis próprias do avaliador.
