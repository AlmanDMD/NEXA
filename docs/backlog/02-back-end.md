# ⚙️ Backlog de Back-end (API & Serviços em Python / FastAPI) — Projeto NEXA
## 50 Cards Exclusivos e Encadeados de Engenharia de Back-end em Python (`BE-001` a `BE-050`)

Este documento contém o planejamento completo e 100% interligado da API RESTful assíncrona desenvolvida em **Python 3.12+ com FastAPI, Pydantic v2 e SQLAlchemy 2.0** do **Sistema Inteligente de Monitoramento do Desempenho Acadêmico — SENAI (NEXA)**, conectando cada serviço ao PostgreSQL (`DB-001`..`DB-050`) e servindo a interface Front-end (`FE-001`..`FE-050`).

---

### Resumo dos Lotes / Sprints de Implementação
- **Lote 1 / Sprint 1 (BE-001 a BE-010)**: Setup Python 3.12+/FastAPI/Uvicorn, Arquitetura em Camadas, Schemas Pydantic v2, Autenticação JWT (PyJWT), Injeção de Dependências (Depends) e RBAC.
- **Lote 2 / Sprint 2 (BE-011 a BE-020)**: APIs de Gestão Acadêmica SENAI (Cursos, Turmas, Disciplinas, Módulos, Matriz de Competências e Matrículas em Lote com SQLAlchemy assíncrono).
- **Lote 3 / Sprint 3 (BE-021 a BE-030)**: APIs de Diário de Classe, Chamada em Lote, Tarefas Práticas de Oficina, Rubricas e Motor de Cálculo de Médias Ponderadas.
- **Lote 4 / Sprint 4 (BE-031 a BE-040)**: APIs de Autoavaliação, Cruzamento Percepção vs. Evidência Prática, Motor Explicável de Alertas Precoces e Endpoints de Dashboard 360°.
- **Lote 5 / Sprint 5 (BE-041 a BE-050)**: Mural de Avisos, Canal Confidencial de Ajuda, Criptografia AES-256 (Cryptography) de Notas Pedagógicas, Gamificação, Exportação CSV/PDF e Swagger/OpenAPI Nativo.

---

### Tabela Geral Encadeada (50 Cards)

| ID | Título | Epic | Prioridade | Estimativa | Lote / Sprint | Dependências |
|---|---|---|---|---|---|---|
| `BE-001` | Configurar Boilerplate Python com FastAPI, Uvicorn e Arquitetura em Camadas | EPIC-01 | P0 | 3 SP | Lote 1 (S1) | `Nenhuma` |
| `BE-002` | Implementar Exception Handlers Globais e Logs Estruturados com Loguru | EPIC-01 | P0 | 2 SP | Lote 1 (S1) | `BE-001` |
| `BE-003` | Configurar Schemas de Validação e Serialização com Pydantic v2 | EPIC-01 | P0 | 2 SP | Lote 1 (S1) | `BE-001, BE-002` |
| `BE-004` | Implementar Serviço de Hash de Senhas e Verificação Criptográfica com Passlib / Bcrypt | EPIC-01 | P0 | 2 SP | Lote 1 (S1) | `BE-001` |
| `BE-005` | Endpoint de Registro e Login com Emissão de Token JWT (PyJWT) e HttpOnly Cookie | EPIC-01 | P0 | 5 SP | Lote 1 (S1) | `BE-003, BE-004, DB-006, DB-008` |
| `BE-006` | Endpoint de Renovação de Sessão via Refresh Token Seguro | EPIC-01 | P0 | 3 SP | Lote 1 (S1) | `BE-005, DB-008` |
| `BE-007` | Endpoint de Logout com Invalidação de Sessão no Banco | EPIC-01 | P0 | 2 SP | Lote 1 (S1) | `BE-005, DB-008` |
| `BE-008` | Dependência FastAPI de Autenticação JWT e Extração de Usuário no Contexto | EPIC-01 | P0 | 3 SP | Lote 1 (S1) | `BE-005` |
| `BE-009` | Dependência de Controle de Acesso por Papel (RBAC: Admin, Coord, Teacher, Student) | EPIC-01 | P0 | 3 SP | Lote 1 (S1) | `BE-008, DB-005` |
| `BE-010` | Endpoint de Consulta do Usuário Autenticado Atual (/api/v1/auth/me) | EPIC-01 | P0 | 2 SP | Lote 1 (S1) | `BE-008, DB-007` |
| `BE-011` | Endpoints CRUD de Cursos Técnicos SENAI com FastAPI e SQLAlchemy | EPIC-02 | P0 | 3 SP | Lote 2 (S2) | `BE-009, DB-011` |
| `BE-012` | Endpoints CRUD de Turmas Acadêmicas e Períodos Letivos | EPIC-02 | P0 | 3 SP | Lote 2 (S2) | `BE-011, DB-012` |
| `BE-013` | Endpoints CRUD de Disciplinas do Currículo Técnico | EPIC-02 | P0 | 3 SP | Lote 2 (S2) | `BE-011, DB-013` |
| `BE-014` | Endpoints para Módulos de Aprendizagem Prática (Tornearia, Metrologia) | EPIC-02 | P0 | 3 SP | Lote 2 (S2) | `BE-013, DB-014` |
| `BE-015` | Endpoints para Gestão de Competências e Habilidades Técnicas | EPIC-04 | P0 | 3 SP | Lote 2 (S2) | `BE-014, DB-015, DB-016` |
| `BE-016` | Endpoint para Matrícula de Estudante em Turma com Validação de Vagas | EPIC-02 | P0 | 3 SP | Lote 2 (S2) | `BE-012, DB-017` |
| `BE-017` | Endpoint para Consulta de Alunos Matriculados por Turma | EPIC-02 | P0 | 2 SP | Lote 2 (S2) | `BE-016, DB-017` |
| `BE-018` | Endpoint para Alocação de Docente em Disciplina/Turma | EPIC-02 | P0 | 2 SP | Lote 2 (S2) | `BE-012, BE-013, DB-018` |
| `BE-019` | Endpoint para Alteração de Status da Matrícula (Ativo, Trancado, Concluído) | EPIC-02 | P1 | 2 SP | Lote 2 (S2) | `BE-016, DB-009, DB-017` |
| `BE-020` | Testes de Integração da Camada de Gestão Acadêmica com Pytest | EPIC-02 | P0 | 5 SP | Lote 2 (S2) | `BE-011, BE-012, BE-013, BE-014, BE-015, BE-016, BE-017, BE-018, BE-019, DB-020` |
| `BE-021` | Endpoint para Registro de Aula Ministrada e Conteúdo Prático | EPIC-03 | P0 | 3 SP | Lote 3 (S3) | `BE-009, BE-018, DB-021` |
| `BE-022` | Endpoint de Chamada Rápida em Lote (Presença e Faltas) | EPIC-03 | P0 | 5 SP | Lote 3 (S3) | `BE-017, BE-021, DB-022` |
| `BE-023` | Endpoint de Consulta de Frequência Consolidada do Aluno | EPIC-03 | P0 | 3 SP | Lote 3 (S3) | `BE-009, BE-022, DB-022, DB-037` |
| `BE-024` | Endpoint para Criação de Atividade Prática com Critérios de Tolerância | EPIC-04 | P0 | 3 SP | Lote 3 (S3) | `BE-014, BE-015, DB-023, DB-024, DB-025` |
| `BE-025` | Endpoint para Registro de Conclusão de Tarefa Prática pelo Docente | EPIC-04 | P0 | 5 SP | Lote 3 (S3) | `BE-024, DB-025, DB-026, DB-033` |
| `BE-026` | Endpoint para Listagem de Tarefas Práticas Pendentes de um Aluno | EPIC-04 | P0 | 3 SP | Lote 3 (S3) | `BE-024, BE-025, DB-025` |
| `BE-027` | Endpoint para Lançamento de Notas de Avaliações Formativas | EPIC-03 | P0 | 3 SP | Lote 3 (S3) | `BE-017, DB-009, DB-027, DB-028` |
| `BE-028` | Endpoint para Fechamento de Médias e Cálculo Ponderado Automático | EPIC-03 | P1 | 5 SP | Lote 3 (S3) | `BE-025, BE-027, DB-014, DB-028` |
| `BE-029` | Middleware / Dependência de Bloqueio de Alteração em Período Letivo Encerrado | EPIC-03 | P1 | 3 SP | Lote 3 (S3) | `BE-012, BE-022, BE-027, DB-029` |
| `BE-030` | Testes Automatizados com Pytest para Cálculos de Médias e Frequência | EPIC-03 | P0 | 3 SP | Lote 3 (S3) | `BE-021, BE-022, BE-023, BE-024, BE-025, BE-026, BE-027, BE-028, BE-029, DB-030` |
| `BE-031` | Endpoint de Dashboard do Professor com Métricas Consolidadas da Turma | EPIC-05 | P0 | 5 SP | Lote 4 (S4) | `BE-028, DB-036, DB-037` |
| `BE-032` | Motor de Regras para Identificação Precoce de Risco Acadêmico (Alerta) | EPIC-05 | P0 | 5 SP | Lote 4 (S4) | `BE-022, BE-025, BE-028, DB-034, DB-036` |
| `BE-033` | Endpoint para Listagem de Alunos em Risco com Justificativa Explicável | EPIC-05 | P0 | 3 SP | Lote 4 (S4) | `BE-032, DB-034` |
| `BE-034` | Endpoint do Portal do Aluno com Progresso e Linha do Tempo (/api/v1/dashboard/student/me) | EPIC-06 | P0 | 5 SP | Lote 4 (S4) | `BE-008, BE-023, BE-026, DB-036, DB-039` |
| `BE-035` | Endpoint para Cadastro de Questionário de Autoavaliação de Competências | EPIC-07 | P1 | 3 SP | Lote 4 (S4) | `BE-014, BE-015, DB-031` |
| `BE-036` | Endpoint para Submissão de Respostas de Autoavaliação pelo Aluno | EPIC-07 | P1 | 3 SP | Lote 4 (S4) | `BE-035, DB-032` |
| `BE-037` | Algoritmo em Python de Cruzamento: Autoavaliação vs Avaliação Prática do Docente | EPIC-07 | P1 | 5 SP | Lote 4 (S4) | `BE-025, BE-032, BE-036, DB-033, DB-035, DB-038` |
| `BE-038` | Endpoint de Consulta de Discrepâncias de Aprendizagem para Apoio Pedagógico | EPIC-07 | P1 | 3 SP | Lote 4 (S4) | `BE-037, DB-035, DB-038` |
| `BE-039` | Endpoint para Resolução e Histórico de Alertas Acadêmicos | EPIC-05 | P1 | 2 SP | Lote 4 (S4) | `BE-032, BE-033, DB-009, DB-034` |
| `BE-040` | Testes de Carga e Performance nas Rotas de Dashboard com Pytest | EPIC-05 | P1 | 3 SP | Lote 4 (S4) | `BE-031, BE-032, BE-033, BE-034, BE-035, BE-036, BE-037, BE-038, BE-039, DB-040` |
| `BE-041` | Endpoint para Publicação de Avisos no Mural da Turma | EPIC-08 | P1 | 2 SP | Lote 5 (S5) | `BE-009, BE-018, DB-041` |
| `BE-042` | Endpoint para Consulta de Mural com Filtro de Turma e Disciplina | EPIC-08 | P1 | 2 SP | Lote 5 (S5) | `BE-041, DB-041` |
| `BE-043` | Endpoint para Abertura de Solicitação de Apoio Confidencial pelo Aluno | EPIC-08 | P0 | 3 SP | Lote 5 (S5) | `BE-009, BE-018, DB-042, DB-044` |
| `BE-044` | Endpoint para Atendimento e Encerramento de Pedidos de Ajuda | EPIC-08 | P0 | 3 SP | Lote 5 (S5) | `BE-043, DB-042, DB-044` |
| `BE-045` | Endpoint para Registro de Observações Pedagógicas com Acesso Restrito e Criptografia | EPIC-08 | P0 | 3 SP | Lote 5 (S5) | `BE-009, DB-009, DB-043` |
| `BE-046` | Endpoint de Conquistas e Badges Desbloqueadas pelo Estudante | EPIC-09 | P2 | 2 SP | Lote 5 (S5) | `BE-008, DB-045, DB-046` |
| `BE-047` | Serviço de Cálculo de Níveis de Habilidade Baseado em Entregas Práticas | EPIC-09 | P2 | 3 SP | Lote 5 (S5) | `BE-025, BE-046, DB-039, DB-045, DB-046` |
| `BE-048` | Middleware / Serviço de Registro de Ações Sensíveis no Log de Auditoria | EPIC-10 | P1 | 3 SP | Lote 5 (S5) | `BE-009, BE-019, BE-027, BE-039, BE-045, DB-009` |
| `BE-049` | Exportação de Relatórios de Desempenho em Formato CSV / PDF com Python | EPIC-10 | P1 | 3 SP | Lote 5 (S5) | `BE-031, DB-036, DB-047` |
| `BE-050` | Documentação OpenAPI/Swagger Nativa do FastAPI e Contrato Final Integrado | EPIC-10 | P0 | 2 SP | Lote 5 (S5) | `BE-001, BE-010, BE-020, BE-030, BE-040, BE-048, BE-049, DB-050` |

---

## Detalhamento Completo e Encadeado dos 50 Cards

### [BE-001] Configurar Boilerplate Python com FastAPI, Uvicorn e Arquitetura em Camadas
- **ID**: `BE-001`
- **Título**: Configurar Boilerplate Python com FastAPI, Uvicorn e Arquitetura em Camadas
- **Área**: Back-end
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `Início da Trilha` | ➡️ Próximo: `BE-002`
- **Dependências Diretas**: `Nenhuma`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: infraestrutura
- **Objetivo**: Estruturar o projeto backend em Python 3.12+ com FastAPI, servidor ASGI Uvicorn e arquitetura em camadas desacopladas (Routers, Services, Repositories, Models e Schemas).
- **Descrição**: Configurar ambiente virtual (Poetry ou venv/pip), setup do FastAPI com suporte a JSON assíncrono, CORS parametrizado via pydantic-settings e .env, lifespan events (startup/shutdown) e injeção de dependências limpa com Depends.
- **História de Usuário**: Como Desenvolvedor Back-end, quero uma base padronizada e moderna em Python, para implementar novos endpoints assíncronos com consistência arquitetural.
- **Critérios de Aceitação**:
- Servidor inicializa com uvicorn app.main:app --reload na porta configurada via .env.
- Estrutura de pastas: app/routers, app/services, app/repositories, app/models, app/schemas, app/core (config/security), app/middlewares.
- Endpoint GET /health retornando status: ok e timestamp UTC.
- **Definição de Pronto (DoD)**: uvicorn app.main:app inicia o servidor FastAPI e responde 200 OK ao healthcheck.
- **Observações Técnicas**: FastAPI oferece alta performance assíncrona, validação nativa com Pydantic v2 e documentação OpenAPI/Swagger automática em /docs.

---

### [BE-002] Implementar Exception Handlers Globais e Logs Estruturados com Loguru
- **ID**: `BE-002`
- **Título**: Implementar Exception Handlers Globais e Logs Estruturados com Loguru
- **Área**: Back-end
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `BE-001` | ➡️ Próximo: `BE-003`
- **Dependências Diretas**: `BE-001`
- **Prioridade**: P0 | **Estimativa**: 2 SP | **Tipo**: feature
- **Objetivo**: Interceptar e tratar centralizadamente todas as exceções da API em Python, retornando respostas JSON padronizadas sem vazar detalhes internos de infraestrutura.
- **Descrição**: Criar classe base AppException herdando de Exception, custom exception_handlers no FastAPI capturando RequestValidationError (Pydantic), SQLAlchemyError (erros de integridade e constraints do Postgres) e exceções 500 genéricas com logging estruturado em JSON via Loguru.
- **História de Usuário**: Como Desenvolvedor Front-end, quero respostas de erro previsíveis e padronizadas (status, code, message, details), para exibir mensagens claras ao usuário.
- **Critérios de Aceitação**:
- Respostas de erro seguem o formato: { success: false, status_code: int, error: str, message: str, details?: list }.
- Erros de validação Pydantic retornam HTTP 400 com lista amigável de campos inválidos.
- Exceções inesperadas são logadas com traceback no servidor e retornam HTTP 500 genérico ao cliente.
- **Definição de Pronto (DoD)**: Testes unitários com pytest cobrindo cenários de erro 400, 401, 403, 404 e 500 passando.
- **Observações Técnicas**: Nunca expor stack traces ou queries SQL cruas em respostas de produção.

---

### [BE-003] Configurar Schemas de Validação e Serialização com Pydantic v2
- **ID**: `BE-003`
- **Título**: Configurar Schemas de Validação e Serialização com Pydantic v2
- **Área**: Back-end
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `BE-002` | ➡️ Próximo: `BE-004`
- **Dependências Diretas**: `BE-001, BE-002`
- **Prioridade**: P0 | **Estimativa**: 2 SP | **Tipo**: feature
- **Objetivo**: Garantir validação estrita de tipos e regras de entrada/saída (body, query params, path params) em todas as rotas da API FastAPI.
- **Descrição**: Configurar schemas base com Pydantic v2 (BaseModel, ConfigDict com from_attributes=True, Field, EmailStr), validadores customizados (@field_validator) com mensagens de erro em português e sanitização de dados.
- **História de Usuário**: Como Engenheiro de Software, quero validar todas as entradas com Pydantic v2, para rejeitar payloads maliciosos ou incompletos antes de tocar o banco de dados.
- **Critérios de Aceitação**:
- Validação automática de payloads rejeitando propriedades extras quando configurado (extra='forbid').
- Mensagens de erro em português para validações comuns (ex: e-mail inválido, senha muito curta).
- Tipagem estrita com Type Hints do Python 3.12.
- **Definição de Pronto (DoD)**: Schemas base configurados e integrados com injeção automática do FastAPI.
- **Observações Técnicas**: Pydantic v2 possui core em Rust, proporcionando até 20x mais performance em validação.

---

### [BE-004] Implementar Serviço de Hash de Senhas e Verificação Criptográfica com Passlib / Bcrypt
- **ID**: `BE-004`
- **Título**: Implementar Serviço de Hash de Senhas e Verificação Criptográfica com Passlib / Bcrypt
- **Área**: Back-end
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `BE-003` | ➡️ Próximo: `BE-005`
- **Dependências Diretas**: `BE-001`
- **Prioridade**: P0 | **Estimativa**: 2 SP | **Tipo**: feature
- **Objetivo**: Proteger as senhas dos usuários utilizando algoritmo moderno de hash com salt aleatório em Python.
- **Descrição**: Implementar app/core/security.py com PasswordHasher utilizando passlib[bcrypt] ou biblioteca bcrypt nativa com fator de custo calibrado (cost rounds = 12), gerando hashes seguros e verificando credenciais em tempo constante.
- **História de Usuário**: Como Usuário do Sistema, quero que minha senha seja criptografada de forma segura, para que mesmo em caso de violação de dados ela não seja descoberta.
- **Critérios de Aceitação**:
- Nenhuma senha em texto puro é trafegada internamente além da validação.
- Comparação de senhas em tempo constante contra timing attacks.
- Testes unitários com senhas corretas e incorretas.
- **Definição de Pronto (DoD)**: Serviço com cobertura de testes unitários com pytest de 100%.
- **Observações Técnicas**: Utilizar bcrypt ou argon2id, respeitando as recomendações da OWASP.

---

### [BE-005] Endpoint de Registro e Login com Emissão de Token JWT (PyJWT) e HttpOnly Cookie
- **ID**: `BE-005`
- **Título**: Endpoint de Registro e Login com Emissão de Token JWT (PyJWT) e HttpOnly Cookie
- **Área**: Back-end
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `BE-004` | ➡️ Próximo: `BE-006`
- **Dependências Diretas**: `BE-003, BE-004, DB-006, DB-008`
- **Prioridade**: P0 | **Estimativa**: 5 SP | **Tipo**: feature
- **Objetivo**: Disponibilizar endpoint de autenticação POST /api/v1/auth/login emitindo access token JWT e refresh token gravado em cookie seguro.
- **Descrição**: Validar credenciais recebidas (email e password) via Pydantic. Em caso de sucesso, gerar Access Token JWT via PyJWT (vida útil de 15 minutos) e Refresh Token (vida útil de 7 dias gravado na tabela auth_sessions). Enviar Refresh Token via cookie com flags httponly=True, secure=True e samesite='lax'.
- **História de Usuário**: Como Usuário, quero fazer login informando meu e-mail e senha, para acessar as funcionalidades autorizadas do meu perfil.
- **Critérios de Aceitação**:
- Rota: POST /api/v1/auth/login.
- Retorno HTTP 200 com { user: { id, email, role, profile }, access_token: str, token_type: 'bearer' }.
- Cookie refresh_token gravado com HttpOnly.
- Retorno HTTP 401 genérico 'Credenciais inválidas' para e-mail inexistente ou senha incorreta.
- **Definição de Pronto (DoD)**: Endpoint testado com pytest e httpx.AsyncClient cobrindo cenários de sucesso e falha.
- **Observações Técnicas**: Mensagem de erro não deve indicar se o erro foi no e-mail ou na senha (prevenção contra account enumeration).

---

### [BE-006] Endpoint de Renovação de Sessão via Refresh Token Seguro
- **ID**: `BE-006`
- **Título**: Endpoint de Renovação de Sessão via Refresh Token Seguro
- **Área**: Back-end
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `BE-005` | ➡️ Próximo: `BE-007`
- **Dependências Diretas**: `BE-005, DB-008`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Permitir que clientes com token JWT expirado obtenham novo Access Token sem necessidade de novo login.
- **Descrição**: Endpoint POST /api/v1/auth/refresh que lê o cookie HttpOnly refresh_token, busca o hash no banco PostgreSQL via SQLAlchemy, valida se não está expirado ou revogado, gera novo par de tokens (token rotation) e invalida o refresh token anterior.
- **História de Usuário**: Como Usuário, quero que minha sessão permaneça ativa enquanto uso o sistema, sem que precise digitar minha senha a cada 15 minutos.
- **Critérios de Aceitação**:
- Rota: POST /api/v1/auth/refresh.
- Sucesso HTTP 200 com novo access_token e novo cookie de refresh.
- Retorno HTTP 401 se token for inválido, revogado ou expirado.
- Detecção de reúso de refresh token revogado (ação de segurança com revogação em cadeia).
- **Definição de Pronto (DoD)**: Fluxo de renovação e rotação de tokens testado e validado.
- **Observações Técnicas**: Refresh token rotation é fundamental para mitigar roubo de tokens em clientes web.

---

### [BE-007] Endpoint de Logout com Invalidação de Sessão no Banco
- **ID**: `BE-007`
- **Título**: Endpoint de Logout com Invalidação de Sessão no Banco
- **Área**: Back-end
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `BE-006` | ➡️ Próximo: `BE-008`
- **Dependências Diretas**: `BE-005, DB-008`
- **Prioridade**: P0 | **Estimativa**: 2 SP | **Tipo**: feature
- **Objetivo**: Encerrar formalmente a sessão do usuário no servidor FastAPI e limpar os cookies do cliente.
- **Descrição**: Endpoint POST /api/v1/auth/logout que recebe o refresh token, atualiza is_revoked = True na tabela auth_sessions e limpa o cookie via response.delete_cookie('refresh_token').
- **História de Usuário**: Como Usuário, quero fazer logout do sistema, garantindo que ninguém possa usar meu acesso no computador da oficina.
- **Critérios de Aceitação**:
- Rota: POST /api/v1/auth/logout.
- Retorno HTTP 200 com { message: 'Sessão encerrada com sucesso' }.
- Cookie refresh_token deletado na resposta HTTP.
- Sessão marcada como revogada no banco de dados.
- **Definição de Pronto (DoD)**: Logout testado e confirmação de que o refresh token anterior é rejeitado após logout.
- **Observações Técnicas**: Essencial para computadores compartilhados em laboratórios SENAI.

---

### [BE-008] Dependência FastAPI de Autenticação JWT e Extração de Usuário no Contexto
- **ID**: `BE-008`
- **Título**: Dependência FastAPI de Autenticação JWT e Extração de Usuário no Contexto
- **Área**: Back-end
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `BE-007` | ➡️ Próximo: `BE-009`
- **Dependências Diretas**: `BE-005`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Interceptar requisições em rotas protegidas, validar o header Authorization Bearer <token> e injetar o usuário autenticado via Depends(get_current_user).
- **Descrição**: Implementar dependência FastAPI get_current_user usando OAuth2PasswordBearer, decodificar assinatura JWT com chave secreta, verificar expiração e carregar objeto User com id, email e role.
- **História de Usuário**: Como Desenvolvedor de Rotas, quero declarar current_user: User = Depends(get_current_user) nas rotas protegidas para acessar o usuário autenticado de forma declarativa.
- **Critérios de Aceitação**:
- Bloqueia requisições sem header Authorization retornando HTTP 401 Unauthorized.
- Bloqueia tokens com assinatura inválida ou expirados com HTTP 401.
- Injeta o objeto User tipado diretamente na assinatura da função do router.
- **Definição de Pronto (DoD)**: Dependência testada e aplicada em rota de exemplo com sucesso.
- **Observações Técnicas**: Aproveita a integração nativa do FastAPI com a especificação OAuth2 para documentar o botão 'Authorize' no Swagger UI.

---

### [BE-009] Dependência de Controle de Acesso por Papel (RBAC: Admin, Coord, Teacher, Student)
- **ID**: `BE-009`
- **Título**: Dependência de Controle de Acesso por Papel (RBAC: Admin, Coord, Teacher, Student)
- **Área**: Back-end
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `BE-008` | ➡️ Próximo: `BE-010`
- **Dependências Diretas**: `BE-008, DB-005`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Restringir o acesso a rotas específicas com base no papel institucional do usuário via injeção de dependência.
- **Descrição**: Criar factory de dependência require_role(*allowed_roles) que verifica current_user.role e lança HTTPException(status_code=403, detail='Acesso não autorizado para seu perfil') caso o papel não seja permitido.
- **História de Usuário**: Como Coordenador Pedagógico, quero que estudantes não possam acessar endpoints de lançamento de notas ou criação de turmas, para manter a segurança do sistema.
- **Critérios de Aceitação**:
- Usuário autenticado sem o papel exigido recebe HTTP 403 Forbidden com mensagem clara.
- Suporte a múltiplos papéis (ex: Depends(require_role('ADMIN', 'COORDINATOR'))).
- Teste cobrindo Aluno tentando acessar rota exclusiva de Professor.
- **Definição de Pronto (DoD)**: Suíte de testes de autorização com perfis distintos passando com pytest.
- **Observações Técnicas**: Permissões contextuais (ex: professor lecionando naquela turma específica) serão complementadas nos services.

---

### [BE-010] Endpoint de Consulta do Usuário Autenticado Atual (/api/v1/auth/me)
- **ID**: `BE-010`
- **Título**: Endpoint de Consulta do Usuário Autenticado Atual (/api/v1/auth/me)
- **Área**: Back-end
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `BE-009` | ➡️ Próximo: `BE-011`
- **Dependências Diretas**: `BE-008, DB-007`
- **Prioridade**: P0 | **Estimativa**: 2 SP | **Tipo**: feature
- **Objetivo**: Permitir que a aplicação cliente obtenha os dados de perfil completos do usuário logado na inicialização.
- **Descrição**: Endpoint GET /api/v1/auth/me protegido por get_current_user. Retorna dados cadastrais do usuário (id, email, role, profile com nome, matrícula e foto) sem expor senhas ou tokens internos.
- **História de Usuário**: Como Usuário do Front-end, quero carregar meus dados de perfil ao abrir a página, para que o sistema mostre meu nome e menu personalizado.
- **Critérios de Aceitação**:
- Rota: GET /api/v1/auth/me.
- Retorno HTTP 200 com perfil completo e matrícula SENAI formatada.
- Retorno HTTP 401 se não autenticado.
- Não expõe password_hash no payload de resposta.
- **Definição de Pronto (DoD)**: Endpoint funcional, serializado via schema Pydantic UserMeResponse e integrado com o banco.
- **Observações Técnicas**: Adicionar cabeçalho Cache-Control: no-store para evitar cache de dados sensíveis.

---

### [BE-011] Endpoints CRUD de Cursos Técnicos SENAI com FastAPI e SQLAlchemy
- **ID**: `BE-011`
- **Título**: Endpoints CRUD de Cursos Técnicos SENAI com FastAPI e SQLAlchemy
- **Área**: Back-end
- **Epic**: EPIC-02: Gestão Acadêmica & Estrutura SENAI
- **Lote / Sprint**: Lote 2 (S2)
- **Sequência na Squad**: ⬅️ Anterior: `BE-010` | ➡️ Próximo: `BE-012`
- **Dependências Diretas**: `BE-009, DB-011`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Disponibilizar endpoints administrativos para cadastro, listagem, atualização e desativação de cursos técnicos.
- **Descrição**: Criar router app/routers/courses.py: GET /api/v1/courses (paginado com busca), POST /api/v1/courses (validação Pydantic do código e carga horária), GET /api/v1/courses/{id} e PUT /api/v1/courses/{id}. Acesso restrito a ADMIN e COORDINATOR via Depends.
- **História de Usuário**: Como Coordenador, quero gerenciar os cursos técnicos da unidade, para organizar a oferta formativa.
- **Critérios de Aceitação**:
- GET /api/v1/courses retorna lista paginada { data, total, page, limit }.
- POST valida se código do curso já existe (rejeita com HTTP 409 se duplicado).
- Exclusão lógica (soft delete via is_active = False).
- **Definição de Pronto (DoD)**: Endpoints implementados com schemas Pydantic e testes de integração pytest.
- **Observações Técnicas**: Impedir desativação de curso caso existam turmas ativas vinculadas.

---

### [BE-012] Endpoints CRUD de Turmas Acadêmicas e Períodos Letivos
- **ID**: `BE-012`
- **Título**: Endpoints CRUD de Turmas Acadêmicas e Períodos Letivos
- **Área**: Back-end
- **Epic**: EPIC-02: Gestão Acadêmica & Estrutura SENAI
- **Lote / Sprint**: Lote 2 (S2)
- **Sequência na Squad**: ⬅️ Anterior: `BE-011` | ➡️ Próximo: `BE-013`
- **Dependências Diretas**: `BE-011, DB-012`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Gerenciar as turmas semestrais, turnos e capacidades de alunos no backend Python.
- **Descrição**: Criar rotas: GET /api/v1/classes (filtros por curso, período letivo e turno), POST /api/v1/classes (validação de datas), GET /api/v1/classes/{id} (detalhes com curso e quantidade de matriculados) e PATCH /api/v1/classes/{id}/status.
- **História de Usuário**: Como Coordenador, quero criar e listar turmas, para alocar os alunos matriculados no semestre.
- **Critérios de Aceitação**:
- Criação de turma vinculada a curso existente (HTTP 404 se curso inválido).
- Validação Pydantic: start_date anterior a end_date.
- Retorno de contagem de matriculados vs max_students.
- **Definição de Pronto (DoD)**: Endpoints funcionais com validação Pydantic e autorização para coordenadores.
- **Observações Técnicas**: Permitir que professores consultem turmas onde lecionam sem precisar de permissão global.

---

### [BE-013] Endpoints CRUD de Disciplinas do Currículo Técnico
- **ID**: `BE-013`
- **Título**: Endpoints CRUD de Disciplinas do Currículo Técnico
- **Área**: Back-end
- **Epic**: EPIC-02: Gestão Acadêmica & Estrutura SENAI
- **Lote / Sprint**: Lote 2 (S2)
- **Sequência na Squad**: ⬅️ Anterior: `BE-012` | ➡️ Próximo: `BE-014`
- **Dependências Diretas**: `BE-011, DB-013`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Disponibilizar endpoints para gestão das unidades curriculares da matriz técnica.
- **Descrição**: Rotas: GET /api/v1/subjects (filtro por course_id), POST /api/v1/subjects, GET /api/v1/subjects/{id} e PUT /api/v1/subjects/{id}. Suporte a ementa técnica e carga horária.
- **História de Usuário**: Como Coordenador Pedagógico, quero cadastrar disciplinas vinculadas aos cursos, para associar os módulos de oficina.
- **Critérios de Aceitação**:
- POST exige nome, código, course_id e carga horária positiva.
- Listagem permite filtrar apenas disciplinas ativas.
- HTTP 400 se carga horária for menor ou igual a zero.
- **Definição de Pronto (DoD)**: Rotas implementadas e documentadas com schemas Pydantic.
- **Observações Técnicas**: Disciplinas podem ser compartilhadas entre turmas do mesmo curso.

---

### [BE-014] Endpoints para Módulos de Aprendizagem Prática (Tornearia, Metrologia)
- **ID**: `BE-014`
- **Título**: Endpoints para Módulos de Aprendizagem Prática (Tornearia, Metrologia)
- **Área**: Back-end
- **Epic**: EPIC-02: Gestão Acadêmica & Estrutura SENAI
- **Lote / Sprint**: Lote 2 (S2)
- **Sequência na Squad**: ⬅️ Anterior: `BE-013` | ➡️ Próximo: `BE-015`
- **Dependências Diretas**: `BE-013, DB-014`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Gerenciar os módulos práticos que compõem uma disciplina técnica SENAI.
- **Descrição**: Rotas: GET /api/v1/subjects/{subject_id}/modules (ordenados por order_index) e POST /api/v1/modules (criação de módulo prático com horas de oficina e nota de corte).
- **História de Usuário**: Como Professor de Prática, quero consultar os módulos da disciplina na ordem didática correta, para registrar as atividades de bancada.
- **Critérios de Aceitação**:
- Módulos retornam ordenados por order_index ascendente.
- Validação Pydantic de passing_score entre 0.00 e 10.00.
- Permissão restrita a docentes alocados e coordenadores.
- **Definição de Pronto (DoD)**: Endpoints testados com módulos práticos de Mecânica e Metrologia.
- **Observações Técnicas**: Permitir reordenação de módulos via PATCH /api/v1/modules/reorder no futuro.

---

### [BE-015] Endpoints para Gestão de Competências e Habilidades Técnicas
- **ID**: `BE-015`
- **Título**: Endpoints para Gestão de Competências e Habilidades Técnicas
- **Área**: Back-end
- **Epic**: EPIC-04: Atividades Práticas de Oficina & Competências
- **Lote / Sprint**: Lote 2 (S2)
- **Sequência na Squad**: ⬅️ Anterior: `BE-014` | ➡️ Próximo: `BE-016`
- **Dependências Diretas**: `BE-014, DB-015, DB-016`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Disponibilizar catálogo de competências técnicas industriais e associação com módulos.
- **Descrição**: Rotas: GET /api/v1/competencies (busca e filtro por categoria), POST /api/v1/competencies, e POST /api/v1/modules/{id}/competencies (vinculando competência a módulo com peso e nível requerido).
- **História de Usuário**: Como Professor, quero associar competências específicas aos módulos práticos, para avaliar se o aluno atingiu o critério de tolerância ou operação de máquina.
- **Critérios de Aceitação**:
- Validação de código único de competência.
- Vinculação módulo-competência com nível requerido entre 1 e 5.
- Consulta com detalhes de competências agregadas por módulo.
- **Definição de Pronto (DoD)**: Rotas criadas com validação de payload no Pydantic v2.
- **Observações Técnicas**: Fundamental para renderizar o gráfico radar (spider chart) no frontend.

---

### [BE-016] Endpoint para Matrícula de Estudante em Turma com Validação de Vagas
- **ID**: `BE-016`
- **Título**: Endpoint para Matrícula de Estudante em Turma com Validação de Vagas
- **Área**: Back-end
- **Epic**: EPIC-02: Gestão Acadêmica & Estrutura SENAI
- **Lote / Sprint**: Lote 2 (S2)
- **Sequência na Squad**: ⬅️ Anterior: `BE-015` | ➡️ Próximo: `BE-017`
- **Dependências Diretas**: `BE-012, DB-017`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Processar a matrícula de um estudante em uma turma garantindo limites de vagas e consistência atômica.
- **Descrição**: Endpoint POST /api/v1/enrollments recebendo student_id e class_id. Executa transação assíncrona SQLAlchemy verificando se a turma está ativa, se o limite max_students não foi atingido e se o aluno já não está matriculado.
- **História de Usuário**: Como Secretaria, quero matricular um aluno em uma turma, garantindo que o limite de capacidade da oficina não seja ultrapassado.
- **Critérios de Aceitação**:
- Rota: POST /api/v1/enrollments.
- HTTP 201 Created se houver vaga e aluno for válido.
- HTTP 409 Conflict se aluno já estiver matriculado.
- HTTP 422 Unprocessable Entity se turma estiver lotada (max_students atingido).
- **Definição de Pronto (DoD)**: Endpoint implementado com transação atômica assíncrona e teste de concorrência.
- **Observações Técnicas**: Garantir isolamento de transação para evitar overbooking de vagas em chamadas simultâneas.

---

### [BE-017] Endpoint para Consulta de Alunos Matriculados por Turma
- **ID**: `BE-017`
- **Título**: Endpoint para Consulta de Alunos Matriculados por Turma
- **Área**: Back-end
- **Epic**: EPIC-02: Gestão Acadêmica & Estrutura SENAI
- **Lote / Sprint**: Lote 2 (S2)
- **Sequência na Squad**: ⬅️ Anterior: `BE-016` | ➡️ Próximo: `BE-018`
- **Dependências Diretas**: `BE-016, DB-017`
- **Prioridade**: P0 | **Estimativa**: 2 SP | **Tipo**: feature
- **Objetivo**: Retornar a lista completa de estudantes de uma turma para montagem da pauta e diário de classe.
- **Descrição**: Endpoint GET /api/v1/classes/{id}/students que retorna lista ordenada alfabeticamente contendo: id do aluno, nome completo, matrícula SENAI, status da matrícula, frequência acumulada e nota parcial.
- **História de Usuário**: Como Professor, quero consultar a lista dos meus alunos de uma turma, para realizar a chamada de presença e registrar tarefas.
- **Critérios de Aceitação**:
- Rota: GET /api/v1/classes/{id}/students.
- Retorno HTTP 200 com array de estudantes e metadados da turma.
- Apenas professores alocados à turma ou coordenadores podem visualizar.
- **Definição de Pronto (DoD)**: Endpoint testado com retorno populado via seed do banco.
- **Observações Técnicas**: Incluir dados do perfil (user_profiles) com join eficiente no SQLAlchemy (selectinload/joinedload) para evitar N+1 queries.

---

### [BE-018] Endpoint para Alocação de Docente em Disciplina/Turma
- **ID**: `BE-018`
- **Título**: Endpoint para Alocação de Docente em Disciplina/Turma
- **Área**: Back-end
- **Epic**: EPIC-02: Gestão Acadêmica & Estrutura SENAI
- **Lote / Sprint**: Lote 2 (S2)
- **Sequência na Squad**: ⬅️ Anterior: `BE-017` | ➡️ Próximo: `BE-019`
- **Dependências Diretas**: `BE-012, BE-013, DB-018`
- **Prioridade**: P0 | **Estimativa**: 2 SP | **Tipo**: feature
- **Objetivo**: Vincular o professor responsável a uma turma e matéria específica.
- **Descrição**: Endpoint POST /api/v1/teacher-assignments recebendo teacher_id, class_id, subject_id e is_main_teacher. Valida se o usuário informado possui a role TEACHER.
- **História de Usuário**: Como Coordenador, quero associar o instrutor de usinagem à sua respectiva oficina e turma, para que ele visualize sua pauta de aulas.
- **Critérios de Aceitação**:
- Rota: POST /api/v1/teacher-assignments.
- HTTP 201 com atribuição criada.
- HTTP 400 se o usuário indicado não for um professor cadastrado.
- HTTP 409 se o professor já estiver atribuído a esta disciplina nesta turma.
- **Definição de Pronto (DoD)**: Endpoint funcional e documentado no Swagger /docs do FastAPI.
- **Observações Técnicas**: Permite registrar múltiplos docentes por oficina para aulas práticas com supervisão compartilhada.

---

### [BE-019] Endpoint para Alteração de Status da Matrícula (Ativo, Trancado, Concluído)
- **ID**: `BE-019`
- **Título**: Endpoint para Alteração de Status da Matrícula (Ativo, Trancado, Concluído)
- **Área**: Back-end
- **Epic**: EPIC-02: Gestão Acadêmica & Estrutura SENAI
- **Lote / Sprint**: Lote 2 (S2)
- **Sequência na Squad**: ⬅️ Anterior: `BE-018` | ➡️ Próximo: `BE-020`
- **Dependências Diretas**: `BE-016, DB-009, DB-017`
- **Prioridade**: P1 | **Estimativa**: 2 SP | **Tipo**: feature
- **Objetivo**: Gerenciar trancamentos, transferências ou conclusões de alunos mantendo integridade histórica.
- **Descrição**: Endpoint PATCH /api/v1/enrollments/{id}/status recebendo o novo status (DROPPED, COMPLETED, SUSPENDED) e justificativa opcional. Registra a mudança no log de auditoria via AuditService.
- **História de Usuário**: Como Secretaria, quero trancar ou concluir a matrícula de um estudante, para que as métricas da turma reflitam apenas alunos ativos.
- **Critérios de Aceitação**:
- Rota: PATCH /api/v1/enrollments/{id}/status.
- HTTP 200 com status atualizado.
- Cria registro em audit_logs com valores antigos e novos serializados em JSON.
- Alunos com status DROPPED deixam de impactar cálculos de faltas futuras.
- **Definição de Pronto (DoD)**: Endpoint testado com verificação de log de auditoria gerado no banco.
- **Observações Técnicas**: Ação restrita a usuários com perfil ADMIN ou COORDINATOR.

---

### [BE-020] Testes de Integração da Camada de Gestão Acadêmica com Pytest
- **ID**: `BE-020`
- **Título**: Testes de Integração da Camada de Gestão Acadêmica com Pytest
- **Área**: Back-end
- **Epic**: EPIC-02: Gestão Acadêmica & Estrutura SENAI
- **Lote / Sprint**: Lote 2 (S2)
- **Sequência na Squad**: ⬅️ Anterior: `BE-019` | ➡️ Próximo: `BE-021`
- **Dependências Diretas**: `BE-011, BE-012, BE-013, BE-014, BE-015, BE-016, BE-017, BE-018, BE-019, DB-020`
- **Prioridade**: P0 | **Estimativa**: 5 SP | **Tipo**: teste
- **Objetivo**: Garantir a confiabilidade e robustez de todos os fluxos de gestão acadêmica implementados no Lote 2.
- **Descrição**: Criar suíte de testes de integração com Pytest e httpx.AsyncClient cobrindo: criação de curso, turma, disciplina, módulo prático, matrícula de estudante com validação de vagas e atribuição de docente.
- **História de Usuário**: Como Tech Lead, quero testes automatizados cobrindo os fluxos acadêmicos, para evitar regressões quando novas rotas forem adicionadas.
- **Critérios de Aceitação**:
- Suíte de testes executa com comando pytest tests/integration/test_academic.py.
- Cobertura mínima de 80% das rotas de gestão acadêmica.
- Testes executam contra banco de dados de testes isolado com rollback após cada teste.
- **Definição de Pronto (DoD)**: Testes passando 100% no terminal e configurados para CI/CD.
- **Observações Técnicas**: Utilizar fixture assíncrona do pytest com transação aninhada para isolamento dos dados de teste.

---

### [BE-021] Endpoint para Registro de Aula Ministrada e Conteúdo Prático
- **ID**: `BE-021`
- **Título**: Endpoint para Registro de Aula Ministrada e Conteúdo Prático
- **Área**: Back-end
- **Epic**: EPIC-03: Diário de Classe: Notas & Frequência
- **Lote / Sprint**: Lote 3 (S3)
- **Sequência na Squad**: ⬅️ Anterior: `BE-020` | ➡️ Próximo: `BE-022`
- **Dependências Diretas**: `BE-009, BE-018, DB-021`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Disponibilizar endpoints POST /api/v1/lessons e GET /api/v1/classes/{class_id}/lessons para criação e consulta do diário de bordo das aulas.
- **Descrição**: Permitir que o professor alocado à turma registre a aula do dia informando class_id, subject_id, module_id, lesson_date, workload_hours (1-8h), topic_summary e lab_environment. Valida se o professor autenticado possui atribuição ativa (teacher_assignments).
- **História de Usuário**: Como Professor, quero abrir o diário do dia informando o módulo e a oficina utilizada, para liberar o lançamento da chamada.
- **Critérios de Aceitação**:
- Rota: POST /api/v1/lessons (Status 201 Created) e GET /api/v1/classes/{class_id}/lessons (Status 200 OK).
- Rejeita com HTTP 403 se um professor tentar criar aula em turma que não leciona.
- Validação Pydantic de data e carga horária.
- **Definição de Pronto (DoD)**: Endpoints de diário funcionais, validados com Pydantic e consumíveis por FE-021.
- **Observações Técnicas**: Ao criar a aula, pré-inicializa a lista de chamada em lote no banco para facilitar o endpoint BE-022.

---

### [BE-022] Endpoint de Chamada Rápida em Lote (Presença e Faltas)
- **ID**: `BE-022`
- **Título**: Endpoint de Chamada Rápida em Lote (Presença e Faltas)
- **Área**: Back-end
- **Epic**: EPIC-03: Diário de Classe: Notas & Frequência
- **Lote / Sprint**: Lote 3 (S3)
- **Sequência na Squad**: ⬅️ Anterior: `BE-021` | ➡️ Próximo: `BE-023`
- **Dependências Diretas**: `BE-017, BE-021, DB-022`
- **Prioridade**: P0 | **Estimativa**: 5 SP | **Tipo**: feature
- **Objetivo**: Implementar endpoint POST /api/v1/lessons/{id}/attendance que registra em uma única transação assíncrona a presença de todos os alunos da turma.
- **Descrição**: Receber payload { records: [{ student_id, status: 'PRESENT' | 'ABSENT' | 'LATE' | 'JUSTIFIED', absent_hours, justification_note }] }. Executar upsert transacional em attendance_records via SQLAlchemy e recalcular imediatamente o attendance_rate na tabela enrollments.
- **História de Usuário**: Como Professor, quero salvar a chamada da turma inteira em 1 clique de forma muito mais rápida que preencher planilhas.
- **Critérios de Aceitação**:
- Rota: POST /api/v1/lessons/{id}/attendance.
- Retorno HTTP 200 com resumo { total_processed, present_count, absent_count, updated_enrollments }.
- Rejeita com HTTP 400 se enviar student_id não matriculado na turma daquela aula.
- Recalcula attendance_rate no servidor (nunca confia em percentual enviado pelo cliente).
- **Definição de Pronto (DoD)**: Endpoint transacional testado e integrado à interface de chamada rápida (FE-022).
- **Observações Técnicas**: Se a frequência atualizada cair abaixo de 78%, aciona avaliação do motor de risco em Python (BE-032).

---

### [BE-023] Endpoint de Consulta de Frequência Consolidada do Aluno
- **ID**: `BE-023`
- **Título**: Endpoint de Consulta de Frequência Consolidada do Aluno
- **Área**: Back-end
- **Epic**: EPIC-03: Diário de Classe: Notas & Frequência
- **Lote / Sprint**: Lote 3 (S3)
- **Sequência na Squad**: ⬅️ Anterior: `BE-022` | ➡️ Próximo: `BE-024`
- **Dependências Diretas**: `BE-009, BE-022, DB-022, DB-037`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Expor endpoint GET /api/v1/students/{id}/attendance com o extrato detalhado de presenças, faltas e margem restante até o limite de 75%.
- **Descrição**: Retornar o histórico de frequência do estudante agrupado por disciplina e módulo prático, consultando a view vw_module_attendance_risk. Aplicar regra de autorização: estudante só consulta seus próprios dados; docentes e coordenação consultam alunos de suas turmas.
- **História de Usuário**: Como Aluno ou Professor, quero consultar o percentual de presença por módulo e saber quantas horas ainda restam antes do limite de reprovação por faltas.
- **Critérios de Aceitação**:
- Rota: GET /api/v1/students/{id}/attendance.
- HTTP 403 Forbidden se um estudante tentar consultar o ID de outro colega (prevenção IDOR).
- Retorna total_hours, attended_hours, absent_hours, attendance_percentage e is_critical (<78%).
- **Definição de Pronto (DoD)**: Endpoint protegido contra IDOR e pronto para consumo em FE-023 e FE-037.
- **Observações Técnicas**: Regra estrita de isolamento de dados de cada aluno (LGPD e privacidade).

---

### [BE-024] Endpoint para Criação de Atividade Prática com Critérios de Tolerância
- **ID**: `BE-024`
- **Título**: Endpoint para Criação de Atividade Prática com Critérios de Tolerância
- **Área**: Back-end
- **Epic**: EPIC-04: Atividades Práticas de Oficina & Competências
- **Lote / Sprint**: Lote 3 (S3)
- **Sequência na Squad**: ⬅️ Anterior: `BE-023` | ➡️ Próximo: `BE-025`
- **Dependências Diretas**: `BE-014, BE-015, DB-023, DB-024, DB-025`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Permitir o cadastro e listagem de tarefas práticas de oficina (ex: Tornearia, Metrologia) juntamente com suas rubricas técnicas em Python.
- **Descrição**: Implementar POST /api/v1/practical-tasks e GET /api/v1/modules/{module_id}/practical-tasks. Na criação, recebe os dados da tarefa e uma lista de critérios (task_criteria) vinculados às competências do módulo. Cria automaticamente registros iniciais PENDING em task_submissions para os alunos ativos da turma.
- **História de Usuário**: Como Instrutor SENAI, quero criar uma atividade prática definindo os critérios de medição e acabamento esperados na bancada.
- **Critérios de Aceitação**:
- Rota: POST /api/v1/practical-tasks (HTTP 201).
- Valida que todas as competências referenciadas nas rubricas existem no banco.
- Gera entregas pendentes para os alunos da turma em transação única assíncrona.
- **Definição de Pronto (DoD)**: Endpoint funcional e integrado com a tela de oficinas práticas (FE-024).
- **Observações Técnicas**: Garante que todo aluno matriculado já enxergue a tarefa no seu painel de pendências (BE-026 / FE-036).

---

### [BE-025] Endpoint para Registro de Conclusão de Tarefa Prática pelo Docente
- **ID**: `BE-025`
- **Título**: Endpoint para Registro de Conclusão de Tarefa Prática pelo Docente
- **Área**: Back-end
- **Epic**: EPIC-04: Atividades Práticas de Oficina & Competências
- **Lote / Sprint**: Lote 3 (S3)
- **Sequência na Squad**: ⬅️ Anterior: `BE-024` | ➡️ Próximo: `BE-026`
- **Dependências Diretas**: `BE-024, DB-025, DB-026, DB-033`
- **Prioridade**: P0 | **Estimativa**: 5 SP | **Tipo**: feature
- **Objetivo**: Permitir que o professor registre rapidamente a conclusão e a avaliação por rubricas de uma peça ou exercício prático feito pelo estudante.
- **Descrição**: Implementar POST /api/v1/tasks/{id}/evaluations recebendo student_id, status ('EVALUATED'), avaliações por critério (criterion_id, achieved_level 1-5, technical_feedback). Calcula a nota ponderada da tarefa no servidor Python, atualiza task_submissions e grava evidência em skill_evidences.
- **História de Usuário**: Como Professor de Oficina, quero avaliar a peça entregue pelo aluno na bancada em poucos toques, gerando a nota e a evidência da competência automaticamente.
- **Critérios de Aceitação**:
- Rota: POST /api/v1/tasks/{id}/evaluations (HTTP 200/201).
- Calcula final_task_score no servidor a partir dos pesos de task_criteria.
- Alimenta automaticamente a tabela skill_evidences (DB-033) para o motor de diagnóstico.
- **Definição de Pronto (DoD)**: Fluxo de avaliação prática testado ponta a ponta e consumível por FE-025 e FE-026.
- **Observações Técnicas**: Evita que o cliente envie nota final manipulada; todo cálculo de tolerância é feito pelo backend Python.

---

### [BE-026] Endpoint para Listagem de Tarefas Práticas Pendentes de um Aluno
- **ID**: `BE-026`
- **Título**: Endpoint para Listagem de Tarefas Práticas Pendentes de um Aluno
- **Área**: Back-end
- **Epic**: EPIC-04: Atividades Práticas de Oficina & Competências
- **Lote / Sprint**: Lote 3 (S3)
- **Sequência na Squad**: ⬅️ Anterior: `BE-025` | ➡️ Próximo: `BE-027`
- **Dependências Diretas**: `BE-024, BE-025, DB-025`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Disponibilizar endpoint GET /api/v1/students/{id}/pending-tasks listando atividades concluídas, pendentes e atrasadas.
- **Descrição**: Consultar task_submissions cruzando com practical_tasks e learning_modules. Marcar dinamicamente como LATE tarefas com status PENDING cujo due_date expirou. Suporta filtros por status (PENDING, LATE, SUBMITTED, EVALUATED) e módulo.
- **História de Usuário**: Como Estudante, quero consultar todas as minhas atividades práticas pendentes e em atraso ordenadas por prazo de entrega.
- **Critérios de Aceitação**:
- Rota: GET /api/v1/students/{id}/pending-tasks.
- Isolamento de segurança: estudante só acessa suas próprias pendências.
- Retorna contadores resumidos { pending_count, late_count, completed_count } e lista ordenada por due_date.
- **Definição de Pronto (DoD)**: Endpoint validado e integrado com o Portal do Aluno (FE-035 e FE-036).
- **Observações Técnicas**: Essencial para o requisito 4.2 (Portal de autonomia do aluno).

---

### [BE-027] Endpoint para Lançamento de Notas de Avaliações Formativas
- **ID**: `BE-027`
- **Título**: Endpoint para Lançamento de Notas de Avaliações Formativas
- **Área**: Back-end
- **Epic**: EPIC-03: Diário de Classe: Notas & Frequência
- **Lote / Sprint**: Lote 3 (S3)
- **Sequência na Squad**: ⬅️ Anterior: `BE-026` | ➡️ Próximo: `BE-028`
- **Dependências Diretas**: `BE-017, DB-009, DB-027, DB-028`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Implementar endpoints para criar avaliações (POST /api/v1/assessments) e lançar notas em lote (POST /api/v1/assessments/{id}/grades).
- **Descrição**: Permitir cadastro de provas e microavaliações teóricas/práticas e lançamento das notas (0.00 a 10.00) e notas de recuperação dos alunos da turma. Registra em audit_logs qualquer retificação de nota já existente.
- **História de Usuário**: Como Professor, quero lançar as notas das avaliações e recuperações de toda a turma em uma única tela tabular.
- **Critérios de Aceitação**:
- Rotas: POST /api/v1/assessments e POST /api/v1/assessments/{id}/grades.
- Validação Pydantic impedindo notas < 0.0 ou > 10.0.
- Verifica se o estudante pertence à turma antes de gravar a nota.
- **Definição de Pronto (DoD)**: Endpoints implementados e integrados com FE-027.
- **Observações Técnicas**: Considera a maior nota entre grade_value e recovery_grade conforme regra pedagógica SENAI.

---

### [BE-028] Endpoint para Fechamento de Médias e Cálculo Ponderado Automático
- **ID**: `BE-028`
- **Título**: Endpoint para Fechamento de Médias e Cálculo Ponderado Automático
- **Área**: Back-end
- **Epic**: EPIC-03: Diário de Classe: Notas & Frequência
- **Lote / Sprint**: Lote 3 (S3)
- **Sequência na Squad**: ⬅️ Anterior: `BE-027` | ➡️ Próximo: `BE-029`
- **Dependências Diretas**: `BE-025, BE-027, DB-014, DB-028`
- **Prioridade**: P1 | **Estimativa**: 5 SP | **Tipo**: feature
- **Objetivo**: Calcular no servidor Python as médias parciais e finais por módulo e disciplina combinando avaliações formativas e entregas práticas de oficina.
- **Descrição**: Implementar POST /api/v1/classes/{id}/calculate-averages e GET /api/v1/classes/{id}/grades-summary. Consolida notas de student_grades (ponderadas por weight) e task_submissions, atualizando final_grade em enrollments e identificando alunos abaixo da nota de corte (passing_score).
- **História de Usuário**: Como Professor ou Coordenador, quero que o sistema calcule automaticamente as médias ponderadas sem fórmulas manuais sujeitas a erro.
- **Critérios de Aceitação**:
- Rota: POST /api/v1/classes/{id}/calculate-averages (HTTP 200).
- Retorna boletim consolidado por aluno e módulo com status (APPROVED, IN_RECOVERY, AT_RISK).
- Precisão numérica de duas casas decimais com arredondamento Decimal do Python.
- **Definição de Pronto (DoD)**: Serviço de cálculo de médias validado com testes unitários e consumido por FE-028.
- **Observações Técnicas**: Aciona automaticamente atualização de indicadores de risco no serviço RiskEngineService (BE-032).

---

### [BE-029] Middleware / Dependência de Bloqueio de Alteração em Período Letivo Encerrado
- **ID**: `BE-029`
- **Título**: Middleware / Dependência de Bloqueio de Alteração em Período Letivo Encerrado
- **Área**: Back-end
- **Epic**: EPIC-03: Diário de Classe: Notas & Frequência
- **Lote / Sprint**: Lote 3 (S3)
- **Sequência na Squad**: ⬅️ Anterior: `BE-028` | ➡️ Próximo: `BE-030`
- **Dependências Diretas**: `BE-012, BE-022, BE-027, DB-029`
- **Prioridade**: P1 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Bloquear requisições de mutação (POST/PUT/PATCH/DELETE) em aulas, frequências, tarefas e notas de turmas já encerradas.
- **Descrição**: Criar dependência FastAPI check_class_is_active que verifica o status da turma. Se for COMPLETED ou ARCHIVED, lança HTTPException(status_code=422, detail='Período letivo encerrado para esta turma'), exceto se reaberto formalmente por um ADMIN.
- **História de Usuário**: Como Coordenador, quero que o backend impeça alterações em diários de turmas já concluídas, exibindo mensagem clara ao professor.
- **Critérios de Aceitação**:
- Intercepta rotas de lançamento de notas, chamadas e avaliações práticas.
- Retorna HTTP 422 com código CLASS_PERIOD_CLOSED.
- Alinhado com a trigger de banco de dados (DB-029).
- **Definição de Pronto (DoD)**: Dependência aplicada e testada com turma em status COMPLETED.
- **Observações Técnicas**: Garante governança acadêmica em dupla camada (API Python + Banco PostgreSQL).

---

### [BE-030] Testes Automatizados com Pytest para Cálculos de Médias e Frequência
- **ID**: `BE-030`
- **Título**: Testes Automatizados com Pytest para Cálculos de Médias e Frequência
- **Área**: Back-end
- **Epic**: EPIC-03: Diário de Classe: Notas & Frequência
- **Lote / Sprint**: Lote 3 (S3)
- **Sequência na Squad**: ⬅️ Anterior: `BE-029` | ➡️ Próximo: `BE-031`
- **Dependências Diretas**: `BE-021, BE-022, BE-023, BE-024, BE-025, BE-026, BE-027, BE-028, BE-029, DB-030`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: teste
- **Objetivo**: Validar com testes unitários e de integração em Python todas as regras matemáticas de frequência (75%), rubricas práticas e médias ponderadas do Lote 3.
- **Descrição**: Criar suíte de testes tests/unit/test_grading.py e tests/integration/test_attendance.py com pytest: cálculo de presença com faltas justificadas vs injustificadas, rubricas de oficina, recuperação, bloqueio de período encerrado e isolamento IDOR.
- **História de Usuário**: Como Tech Lead, quero 100% de confiança nos cálculos de notas e faltas do sistema antes de construir os dashboards analíticos.
- **Critérios de Aceitação**:
- Testes unitários e de integração do Lote 3 passando sem erros via pytest.
- Casos de borda testados (nota 0, nota 10, 0 aulas dadas, 100% faltas).
- Verificação de segurança impedindo Aluno A de ver notas/faltas do Aluno B.
- **Definição de Pronto (DoD)**: Suíte de testes do Lote 3 verde no pipeline de testes.
- **Observações Técnicas**: Fecha o ciclo de back-end do Lote 3 (Sprint S3).

---

### [BE-031] Endpoint de Dashboard do Professor com Métricas Consolidadas da Turma
- **ID**: `BE-031`
- **Título**: Endpoint de Dashboard do Professor com Métricas Consolidadas da Turma
- **Área**: Back-end
- **Epic**: EPIC-05: Dashboard Híbrido do Professor & Visão 360°
- **Lote / Sprint**: Lote 4 (S4)
- **Sequência na Squad**: ⬅️ Anterior: `BE-030` | ➡️ Próximo: `BE-032`
- **Dependências Diretas**: `BE-028, DB-036, DB-037`
- **Prioridade**: P0 | **Estimativa**: 5 SP | **Tipo**: feature
- **Objetivo**: Disponibilizar endpoint GET /api/v1/dashboard/teacher/classes/{id} e GET /api/v1/students/{id}/360 com visão híbrida da turma e ficha 360° do aluno.
- **Descrição**: Consultar vw_student_360_performance via SQLAlchemy assíncrono e agregar KPIs: média geral da turma, taxa média de presença, percentual de entregas práticas no prazo, distribuição por módulo (Desenho Técnico, Metrologia, Tornearia) e contagem de alunos em risco.
- **História de Usuário**: Como Professor, quero abrir meu dashboard e enxergar imediatamente o panorama da turma em todos os módulos e a ficha completa de cada aluno.
- **Critérios de Aceitação**:
- Rotas: GET /api/v1/dashboard/teacher/classes/{id} e GET /api/v1/students/{id}/360.
- Retorna KPIs globais, evolução por módulo e lista de estudantes com indicadores.
- Tempo de resposta < 150ms utilizando a view DB-036.
- **Definição de Pronto (DoD)**: Endpoints de dashboard implementados e prontos para FE-031, FE-033 e FE-034.
- **Observações Técnicas**: Atende diretamente ao requisito 4.1 (Dashboard híbrido para professores).

---

### [BE-032] Motor de Regras para Identificação Precoce de Risco Acadêmico (Alerta)
- **ID**: `BE-032`
- **Título**: Motor de Regras para Identificação Precoce de Risco Acadêmico (Alerta)
- **Área**: Back-end
- **Epic**: EPIC-05: Dashboard Híbrido do Professor & Visão 360°
- **Lote / Sprint**: Lote 4 (S4)
- **Sequência na Squad**: ⬅️ Anterior: `BE-031` | ➡️ Próximo: `BE-033`
- **Dependências Diretas**: `BE-022, BE-025, BE-028, DB-034, DB-036`
- **Prioridade**: P0 | **Estimativa**: 5 SP | **Tipo**: feature
- **Objetivo**: Implementar serviço em Python transparente e explicável (RiskEngineService) que analisa frequência, notas e pendências práticas para gerar alertas precoces.
- **Descrição**: Implementar regras determinísticas e auditáveis em Python: (1) Presença < 75% -> CRITICAL; Presença entre 75% e 78% -> HIGH; (2) >= 2 tarefas práticas atrasadas (LATE) -> MODERATE/HIGH; (3) Média parcial abaixo de passing_score -> HIGH. Grava/atualiza registros em academic_alerts com explainable_reason detalhado.
- **História de Usuário**: Como Professor e Coordenador, quero que o sistema identifique precocemente alunos que precisam de apoio pedagógico, explicando exatamente qual regra disparou o alerta.
- **Critérios de Aceitação**:
- Nenhuma decisão de caixa-preta: todo alerta possui explainable_reason legível e metric_snapshot em formato JSON.
- Evita alertas duplicados abertos para o mesmo motivo e aluno.
- Apresenta o alerta como indicador de atenção pedagógica, nunca como reprovação automática.
- **Definição de Pronto (DoD)**: Motor de risco testado unitariamente com pytest com todos os graus (LOW, MODERATE, HIGH, CRITICAL).
- **Observações Técnicas**: Respeita estritamente a diretriz ética da seção 14 e 16 (regras transparentes e explicáveis).

---

### [BE-033] Endpoint para Listagem de Alunos em Risco com Justificativa Explicável
- **ID**: `BE-033`
- **Título**: Endpoint para Listagem de Alunos em Risco com Justificativa Explicável
- **Área**: Back-end
- **Epic**: EPIC-05: Dashboard Híbrido do Professor & Visão 360°
- **Lote / Sprint**: Lote 4 (S4)
- **Sequência na Squad**: ⬅️ Anterior: `BE-032` | ➡️ Próximo: `BE-034`
- **Dependências Diretas**: `BE-032, DB-034`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Expor endpoint GET /api/v1/dashboard/teacher/at-risk listando os estudantes que necessitam de acompanhamento prioritário.
- **Descrição**: Retornar lista paginada e filtrável (por class_id, module_id, risk_level, alert_category) de alertas ativos em academic_alerts, trazendo dados do aluno, motivo explicável, métricas atuais e sugestão de ação pedagógica (ex: 'Agendar mentoria prática no módulo de Metrologia').
- **História de Usuário**: Como Professor, quero filtrar os alunos em situação de risco na minha turma e ler o motivo detalhado para planejar uma intervenção oportuna.
- **Critérios de Aceitação**:
- Rota: GET /api/v1/dashboard/teacher/at-risk (HTTP 200).
- Ordenação padrão por severidade (CRITICAL -> HIGH -> MODERATE -> LOW).
- Restrito a professores das respectivas turmas e coordenadores.
- **Definição de Pronto (DoD)**: Endpoint funcional e integrado ao card de alunos em risco (FE-032).
- **Observações Técnicas**: Permite acionar criação rápida de observação pedagógica ou convite de mentoria.

---

### [BE-034] Endpoint do Portal do Aluno com Progresso e Linha do Tempo (/api/v1/dashboard/student/me)
- **ID**: `BE-034`
- **Título**: Endpoint do Portal do Aluno com Progresso e Linha do Tempo (/api/v1/dashboard/student/me)
- **Área**: Back-end
- **Epic**: EPIC-06: Portal de Autonomia do Aluno & Pendências
- **Lote / Sprint**: Lote 4 (S4)
- **Sequência na Squad**: ⬅️ Anterior: `BE-033` | ➡️ Próximo: `BE-035`
- **Dependências Diretas**: `BE-008, BE-023, BE-026, DB-036, DB-039`
- **Prioridade**: P0 | **Estimativa**: 5 SP | **Tipo**: feature
- **Objetivo**: Disponibilizar endpoint GET /api/v1/dashboard/student/me reunindo todas as informações privadas do próprio estudante autenticado.
- **Descrição**: Retornar para o aluno logado: resumo de frequência e médias por disciplina, progresso percentual em cada módulo prático, evolução de nível por competência técnica (dados para o gráfico radar), contadores de atividades e linha do tempo (student_milestone_history).
- **História de Usuário**: Como Estudante, quero acessar meu painel privado e acompanhar minha evolução de habilidades, notas, frequência e marcos conquistados.
- **Critérios de Aceitação**:
- Rota: GET /api/v1/dashboard/student/me (HTTP 200).
- Usa exclusivamente o ID extraído do token JWT (current_user.id), impossibilitando acesso a dados de terceiros.
- Nunca expõe observações pedagógicas restritas dos professores.
- **Definição de Pronto (DoD)**: Endpoint testado e integrado às telas do Portal do Aluno (FE-035, FE-037, FE-038 e FE-039).
- **Observações Técnicas**: Cumpre os requisitos de privacidade e autonomia do estudante (seção 4.2).

---

### [BE-035] Endpoint para Cadastro de Questionário de Autoavaliação de Competências
- **ID**: `BE-035`
- **Título**: Endpoint para Cadastro de Questionário de Autoavaliação de Competências
- **Área**: Back-end
- **Epic**: EPIC-07: Autoavaliação & Motor de Diagnóstico Explicável
- **Lote / Sprint**: Lote 4 (S4)
- **Sequência na Squad**: ⬅️ Anterior: `BE-034` | ➡️ Próximo: `BE-036`
- **Dependências Diretas**: `BE-014, BE-015, DB-031`
- **Prioridade**: P1 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Permitir que professores criem e ativem ciclos de autoavaliação vinculados às competências de um módulo prático.
- **Descrição**: Implementar POST /api/v1/self-assessments/forms e GET /api/v1/classes/{class_id}/self-assessments/forms. Retorna para o formulário a lista de competências associadas ao módulo (module_competencies) com suas descrições e escala de 1 a 5.
- **História de Usuário**: Como Professor, quero disponibilizar o questionário de autoavaliação de um módulo para minha turma responder.
- **Critérios de Aceitação**:
- Criação valida se o módulo possui competências cadastradas.
- Valida janela de abertura e fechamento (opens_at < closes_at).
- Lista formulários pendentes de resposta para o aluno logado.
- **Definição de Pronto (DoD)**: Endpoints implementados e documentados para consumo em FE-041.
- **Observações Técnicas**: Suporta reabertura de prazo pelo professor caso necessário.

---

### [BE-036] Endpoint para Submissão de Respostas de Autoavaliação pelo Aluno
- **ID**: `BE-036`
- **Título**: Endpoint para Submissão de Respostas de Autoavaliação pelo Aluno
- **Área**: Back-end
- **Epic**: EPIC-07: Autoavaliação & Motor de Diagnóstico Explicável
- **Lote / Sprint**: Lote 4 (S4)
- **Sequência na Squad**: ⬅️ Anterior: `BE-035` | ➡️ Próximo: `BE-037`
- **Dependências Diretas**: `BE-035, DB-032`
- **Prioridade**: P1 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Receber e persistir a autoavaliação de habilidades práticas enviada pelo estudante autenticado.
- **Descrição**: Implementar POST /api/v1/self-assessments/submit recebendo form_id e lista de respostas [{ competency_id, perceived_level (1-5), confidence_score (1-5), difficulty_notes }]. Grava em student_self_assessments e dispara o algoritmo de cruzamento diagnóstico (BE-037).
- **História de Usuário**: Como Estudante, quero enviar minha autoavaliação das habilidades práticas do módulo e relatar dificuldades que tive nas máquinas.
- **Critérios de Aceitação**:
- Rota: POST /api/v1/self-assessments/submit (HTTP 201).
- Valida se o formulário está ativo e dentro do prazo.
- Impede submissão em nome de outro aluno (usa current_user.id).
- **Definição de Pronto (DoD)**: Submissão testada e integrada à tela de autoavaliação do aluno (FE-041).
- **Observações Técnicas**: Caso o aluno relate dificuldade alta (perceived_level <= 2), sugere abertura opcional de pedido de ajuda.

---

### [BE-037] Algoritmo em Python de Cruzamento: Autoavaliação vs Avaliação Prática do Docente
- **ID**: `BE-037`
- **Título**: Algoritmo em Python de Cruzamento: Autoavaliação vs Avaliação Prática do Docente
- **Área**: Back-end
- **Epic**: EPIC-07: Autoavaliação & Motor de Diagnóstico Explicável
- **Lote / Sprint**: Lote 4 (S4)
- **Sequência na Squad**: ⬅️ Anterior: `BE-036` | ➡️ Próximo: `BE-038`
- **Dependências Diretas**: `BE-025, BE-032, BE-036, DB-033, DB-035, DB-038`
- **Prioridade**: P1 | **Estimativa**: 5 SP | **Tipo**: feature
- **Objetivo**: Implementar o motor de comparação entre a autoavaliação do estudante e as evidências práticas registradas pelo professor.
- **Descrição**: Criar DiagnosticService em Python que consulta vw_self_eval_discrepancy (DB-038). Para cada competência: (1) Se |perceived - verified| <= 0.8 -> ALIGNED; (2) Se perceived - verified >= 1.5 -> OVERCONFIDENCE_RISK (aluno acha que domina, mas falhou na prática/tolerância); (3) Se verified - perceived >= 1.5 -> UNDERCONFIDENCE_SUPPORT (aluno domina a prática, mas está inseguro); (4) Sem entregas avaliadas -> INSUFFICIENT_EVIDENCE. Grava em explainable_diagnostics com critérios, evidências e limitações explícitas.
- **História de Usuário**: Como Professor, quero um diagnóstico explicável que compare a autoavaliação do aluno com as notas práticas reais, destacando divergências que mereçam mentoria.
- **Critérios de Aceitação**:
- Nunca trata autoavaliação como prova definitiva de competência.
- Todo diagnóstico gerado inclui explanation_text, evidências utilizadas e limitations_note.
- Gera alerta pedagógico quando houver divergência crítica em competência de segurança ou precisão.
- **Definição de Pronto (DoD)**: Motor de diagnóstico coberto por testes unitários com pytest validando os 4 cenários.
- **Observações Técnicas**: Atende com excelência todos os requisitos da seção 4.3 (diagnóstico explicável sem rótulos).

---

### [BE-038] Endpoint de Consulta de Discrepâncias de Aprendizagem para Apoio Pedagógico
- **ID**: `BE-038`
- **Título**: Endpoint de Consulta de Discrepâncias de Aprendizagem para Apoio Pedagógico
- **Área**: Back-end
- **Epic**: EPIC-07: Autoavaliação & Motor de Diagnóstico Explicável
- **Lote / Sprint**: Lote 4 (S4)
- **Sequência na Squad**: ⬅️ Anterior: `BE-037` | ➡️ Próximo: `BE-039`
- **Dependências Diretas**: `BE-037, DB-035, DB-038`
- **Prioridade**: P1 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Disponibilizar endpoint GET /api/v1/diagnostics/discrepancies para visualização comparativa entre autoavaliação e evidências acadêmicas.
- **Descrição**: Permitir consultar os diagnósticos explicáveis por turma, módulo ou estudante individual. Retorna para cada competência: nível autoavaliado, nível verificado pelo professor, lista de evidências práticas que embasam a nota, tipo de divergência, texto explicativo e limitações.
- **História de Usuário**: Como Professor ou Aluno, quero visualizar o comparativo entre a autoavaliação e as avaliações práticas para orientar o estudo e a mentoria.
- **Critérios de Aceitação**:
- Rota: GET /api/v1/diagnostics/discrepancies.
- Estudante visualiza apenas o próprio comparativo com linguagem construtiva.
- Professor visualiza o mapa de divergências de toda a turma com filtros.
- **Definição de Pronto (DoD)**: Endpoint funcional e integrado ao componente comparativo (FE-042).
- **Observações Técnicas**: Linguagem pedagógica construtiva, sem rotular estudantes permanentemente.

---

### [BE-039] Endpoint para Resolução e Histórico de Alertas Acadêmicos
- **ID**: `BE-039`
- **Título**: Endpoint para Resolução e Histórico de Alertas Acadêmicos
- **Área**: Back-end
- **Epic**: EPIC-05: Dashboard Híbrido do Professor & Visão 360°
- **Lote / Sprint**: Lote 4 (S4)
- **Sequência na Squad**: ⬅️ Anterior: `BE-038` | ➡️ Próximo: `BE-040`
- **Dependências Diretas**: `BE-032, BE-033, DB-009, DB-034`
- **Prioridade**: P1 | **Estimativa**: 2 SP | **Tipo**: feature
- **Objetivo**: Permitir que professores e coordenadores assumam o acompanhamento (ACKNOWLEDGE) ou encerrem (RESOLVE) alertas acadêmicos após intervenção.
- **Descrição**: Implementar PATCH /api/v1/alerts/{id}/resolve recebendo status ('ACKNOWLEDGED' | 'RESOLVED') e resolution_notes obrigatórias descrevendo a ação pedagógica tomada. Registra auditoria em audit_logs.
- **História de Usuário**: Como Professor, quero registrar qual intervenção realizei para apoiar um aluno em alerta e marcar o acompanhamento como concluído.
- **Critérios de Aceitação**:
- Rota: PATCH /api/v1/alerts/{id}/resolve (HTTP 200).
- Exige preenchimento de resolution_notes (mínimo 10 caracteres).
- Grava resolved_by com o ID do professor autenticado.
- **Definição de Pronto (DoD)**: Endpoint testado e integrado às ações rápidas do card de risco (FE-032).
- **Observações Técnicas**: Mantém o histórico completo de intervenções na ficha 360° do aluno.

---

### [BE-040] Testes de Carga e Performance nas Rotas de Dashboard com Pytest
- **ID**: `BE-040`
- **Título**: Testes de Carga e Performance nas Rotas de Dashboard com Pytest
- **Área**: Back-end
- **Epic**: EPIC-05: Dashboard Híbrido do Professor & Visão 360°
- **Lote / Sprint**: Lote 4 (S4)
- **Sequência na Squad**: ⬅️ Anterior: `BE-039` | ➡️ Próximo: `BE-041`
- **Dependências Diretas**: `BE-031, BE-032, BE-033, BE-034, BE-035, BE-036, BE-037, BE-038, BE-039, DB-040`
- **Prioridade**: P1 | **Estimativa**: 3 SP | **Tipo**: teste
- **Objetivo**: Validar a corretude, segurança e tempo de resposta de todas as rotas analíticas, dashboards e diagnósticos do Lote 4 em Python.
- **Descrição**: Criar suíte de testes automatizados com pytest e httpx verificando: motor de risco (BE-032), cruzamento diagnóstico (BE-037), isolamento de dados no portal do aluno (BE-034) e tempo de resposta (<200ms) com dados do seed.
- **História de Usuário**: Como Tech Lead, quero garantir que os dashboards e motores de diagnóstico em Python respondam rápido e sem falhas de segurança.
- **Critérios de Aceitação**:
- Cobertura >= 80% nos serviços RiskEngineService e DiagnosticService.
- Confirmação de zero vazamento de dados entre estudantes.
- Tempo de resposta médio das rotas de dashboard abaixo de 200ms.
- **Definição de Pronto (DoD)**: Suíte de testes do Lote 4 passando 100% no pytest.
- **Observações Técnicas**: Conclui o Lote 4 (Sprint S4) do Back-end.

---

### [BE-041] Endpoint para Publicação de Avisos no Mural da Turma
- **ID**: `BE-041`
- **Título**: Endpoint para Publicação de Avisos no Mural da Turma
- **Área**: Back-end
- **Epic**: EPIC-08: Comunicação Oficial & Solicitações Confidenciais
- **Lote / Sprint**: Lote 5 (S5)
- **Sequência na Squad**: ⬅️ Anterior: `BE-040` | ➡️ Próximo: `BE-042`
- **Dependências Diretas**: `BE-009, BE-018, DB-041`
- **Prioridade**: P1 | **Estimativa**: 2 SP | **Tipo**: feature
- **Objetivo**: Permitir que professores e coordenadores publiquem, editem ou fixem comunicados oficiais direcionados a uma turma ou disciplina.
- **Descrição**: Implementar POST /api/v1/announcements, PATCH /api/v1/announcements/{id} e DELETE /api/v1/announcements/{id}. Valida se o autor é professor da turma ou coordenador. Suporta prioridade (NORMAL, IMPORTANT, URGENT) e fixação no topo (is_pinned).
- **História de Usuário**: Como Professor, quero publicar avisos oficiais para minha turma sobre aulas práticas, materiais e avaliações.
- **Critérios de Aceitação**:
- Rota: POST /api/v1/announcements (HTTP 201 Created).
- Bloqueia criação de avisos por usuários com perfil STUDENT (HTTP 403).
- Validação Pydantic de título, conteúdo e class_id.
- **Definição de Pronto (DoD)**: Endpoint funcional e integrado ao mural (FE-043).
- **Observações Técnicas**: Atende ao requisito 4.4 (Canal oficial de comunicação - Mural de avisos).

---

### [BE-042] Endpoint para Consulta de Mural com Filtro de Turma e Disciplina
- **ID**: `BE-042`
- **Título**: Endpoint para Consulta de Mural com Filtro de Turma e Disciplina
- **Área**: Back-end
- **Epic**: EPIC-08: Comunicação Oficial & Solicitações Confidenciais
- **Lote / Sprint**: Lote 5 (S5)
- **Sequência na Squad**: ⬅️ Anterior: `BE-041` | ➡️ Próximo: `BE-043`
- **Dependências Diretas**: `BE-041, DB-041`
- **Prioridade**: P1 | **Estimativa**: 2 SP | **Tipo**: feature
- **Objetivo**: Disponibilizar endpoint GET /api/v1/announcements retornando os avisos das turmas às quais o usuário pertence.
- **Descrição**: Retornar avisos ordenados por is_pinned DESC e published_at DESC, com suporte a paginação e filtro por class_id, subject_id e priority. Estudantes visualizam apenas avisos das turmas em que estão matriculados.
- **História de Usuário**: Como Estudante ou Professor, quero consultar os avisos da minha turma filtrando por disciplina.
- **Critérios de Aceitação**:
- Rota: GET /api/v1/announcements (HTTP 200 OK).
- Filtra automaticamente avisos expirados (expires_at < now_utc()).
- Isolamento por turma: aluno de outra turma recebe HTTP 403 se tentar filtrar turma alheia.
- **Definição de Pronto (DoD)**: Consulta de mural testada e pronta para FE-043.
- **Observações Técnicas**: Usa o índice composto criado em DB-041 para resposta imediata.

---

### [BE-043] Endpoint para Abertura de Solicitação de Apoio Confidencial pelo Aluno
- **ID**: `BE-043`
- **Título**: Endpoint para Abertura de Solicitação de Apoio Confidencial pelo Aluno
- **Área**: Back-end
- **Epic**: EPIC-08: Comunicação Oficial & Solicitações Confidenciais
- **Lote / Sprint**: Lote 5 (S5)
- **Sequência na Squad**: ⬅️ Anterior: `BE-042` | ➡️ Próximo: `BE-044`
- **Dependências Diretas**: `BE-009, BE-018, DB-042, DB-044`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Permitir que o estudante solicite ajuda ou mentoria pedagógica a um professor com garantia de confidencialidade perante outros alunos.
- **Descrição**: Implementar POST /api/v1/help-requests e GET /api/v1/help-requests. O aluno informa subject_id, module_id opcional, category, subject_title, description e is_confidential (default True). Na listagem GET, um estudante vê estritamente os próprios pedidos; o professor vê os pedidos das suas disciplinas.
- **História de Usuário**: Como Estudante, quero enviar um pedido de ajuda confidencial ao professor sobre uma dificuldade prática sem que nenhum outro colega tenha acesso.
- **Critérios de Aceitação**:
- Rota: POST /api/v1/help-requests (HTTP 201 Created).
- Proteção anti-exposição: nenhum endpoint retorna help_requests de um aluno para outro estudante.
- Direciona automaticamente ao professor titular da disciplina na turma.
- **Definição de Pronto (DoD)**: Endpoints de solicitação de ajuda testados e integrados a FE-044.
- **Observações Técnicas**: Requisito crítico de segurança e privacidade (seção 4.4 e seção 14).

---

### [BE-044] Endpoint para Atendimento e Encerramento de Pedidos de Ajuda
- **ID**: `BE-044`
- **Título**: Endpoint para Atendimento e Encerramento de Pedidos de Ajuda
- **Área**: Back-end
- **Epic**: EPIC-08: Comunicação Oficial & Solicitações Confidenciais
- **Lote / Sprint**: Lote 5 (S5)
- **Sequência na Squad**: ⬅️ Anterior: `BE-043` | ➡️ Próximo: `BE-045`
- **Dependências Diretas**: `BE-043, DB-042, DB-044`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Permitir a troca de mensagens internas no chamado, atualização de status de leitura/atendimento e encerramento da solicitação de ajuda.
- **Descrição**: Implementar POST /api/v1/help-requests/{id}/messages (envio de mensagem em chat_messages com atualização de leitura) e PATCH /api/v1/help-requests/{id} (transição de status: OPEN -> IN_PROGRESS -> RESOLVED -> CLOSED com resolution_summary).
- **História de Usuário**: Como Professor, quero responder ao pedido de ajuda do aluno, agendar uma mentoria e registrar o encerramento quando a dúvida for sanada.
- **Critérios de Aceitação**:
- Valida que apenas o aluno autor do pedido, o professor responsável ou a coordenação podem ler ou enviar mensagens no chamado.
- Atualiza is_read = True e read_at quando o destinatário visualiza as mensagens.
- Registra closed_at ao encerrar a solicitação.
- **Definição de Pronto (DoD)**: Fluxo completo de mensagens e estados de solicitação validado e integrado a FE-044 e FE-045.
- **Observações Técnicas**: Cumpre o controle de estados de leitura, resposta e encerramento (seção 4.4).

---

### [BE-045] Endpoint para Registro de Observações Pedagógicas com Acesso Restrito e Criptografia
- **ID**: `BE-045`
- **Título**: Endpoint para Registro de Observações Pedagógicas com Acesso Restrito e Criptografia
- **Área**: Back-end
- **Epic**: EPIC-08: Comunicação Oficial & Solicitações Confidenciais
- **Lote / Sprint**: Lote 5 (S5)
- **Sequência na Squad**: ⬅️ Anterior: `BE-044` | ➡️ Próximo: `BE-046`
- **Dependências Diretas**: `BE-009, DB-009, DB-043`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Disponibilizar endpoints estritamente protegidos para docentes e coordenadores registrarem e consultarem observações pedagógicas sobre estudantes com suporte a criptografia.
- **Descrição**: Implementar POST /api/v1/pedagogical-notes e GET /api/v1/students/{id}/pedagogical-notes. Bloqueia terminantemente qualquer acesso por usuários com role STUDENT. Filtra o retorno conforme visibility_scope (PRIVATE_AUTHOR, TEACHERS_AND_COORD, COORDINATION_ONLY) e criptografa anotações sensíveis usando cryptography (Fernet / AES-256).
- **História de Usuário**: Como Professor ou Coordenador, quero registrar anotações pedagógicas de acompanhamento sabendo que dados sensíveis estão criptografados e com controle estrito de quem pode visualizá-los.
- **Critérios de Aceitação**:
- Qualquer tentativa de acesso por perfil STUDENT retorna HTTP 403 Forbidden e gera alerta em audit_logs.
- Respeita rigorosamente o visibility_scope de cada nota.
- Suporta agendamento de acompanhamento (requires_followup e followup_date).
- **Definição de Pronto (DoD)**: Endpoint auditado com testes de isolamento de permissão e integrado a FE-046.
- **Observações Técnicas**: Jamais incluir pedagogical_notes em payloads enviados para o portal do aluno.

---

### [BE-046] Endpoint de Conquistas e Badges Desbloqueadas pelo Estudante
- **ID**: `BE-046`
- **Título**: Endpoint de Conquistas e Badges Desbloqueadas pelo Estudante
- **Área**: Back-end
- **Epic**: EPIC-09: Gamificação Pedagógica Transparente & Níveis
- **Lote / Sprint**: Lote 5 (S5)
- **Sequência na Squad**: ⬅️ Anterior: `BE-045` | ➡️ Próximo: `BE-047`
- **Dependências Diretas**: `BE-008, DB-045, DB-046`
- **Prioridade**: P2 | **Estimativa**: 2 SP | **Tipo**: feature
- **Objetivo**: Expor endpoint GET /api/v1/gamification/badges retornando as insígnias conquistadas, próximas conquistas e critérios transparentes de pontuação.
- **Descrição**: Retornar o catálogo de gamification_badges cruzado com student_achievements do estudante autenticado, indicando percentual de progresso para cada conquista, XP total acumulado, nível atual de habilidade e explicação clara da regra de pontuação.
- **História de Usuário**: Como Estudante, quero visualizar minhas insígnias desbloqueadas e entender exatamente o que falta para conquistar as próximas.
- **Critérios de Aceitação**:
- Rota: GET /api/v1/gamification/badges (HTTP 200).
- Exibe criteria_explanation de todas as badges.
- Não expõe ranking vexatório de alunos com menor pontuação.
- **Definição de Pronto (DoD)**: Endpoint funcional e pronto para consumo na tela de conquistas (FE-047).
- **Observações Técnicas**: Atende ao requisito 4.2 (Gamificação transparente e sem exposição indevida).

---

### [BE-047] Serviço de Cálculo de Níveis de Habilidade Baseado em Entregas Práticas
- **ID**: `BE-047`
- **Título**: Serviço de Cálculo de Níveis de Habilidade Baseado em Entregas Práticas
- **Área**: Back-end
- **Epic**: EPIC-09: Gamificação Pedagógica Transparente & Níveis
- **Lote / Sprint**: Lote 5 (S5)
- **Sequência na Squad**: ⬅️ Anterior: `BE-046` | ➡️ Próximo: `BE-048`
- **Dependências Diretas**: `BE-025, BE-046, DB-039, DB-045, DB-046`
- **Prioridade**: P2 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Automatizar em Python a concessão de XP, evolução de nível (Iniciante, Praticante, Proficiente, Especialista) e desbloqueio de badges quando o aluno conclui módulos e práticas.
- **Descrição**: Criar GamificationService acionado após avaliação prática (BE-025) e fechamento de módulo (BE-028). Verifica se os critérios objetivos de gamification_badges foram atingidos, grava em student_achievements e adiciona marco em student_milestone_history.
- **História de Usuário**: Como Estudante, quero subir de nível e desbloquear conquistas automaticamente quando minhas peças práticas forem aprovadas pelo professor.
- **Critérios de Aceitação**:
- Regra de pontuação determinística, documentada e calculada 100% no servidor Python.
- Idempotente: não concede a mesma badge duas vezes ao mesmo aluno.
- Registra marco na linha do tempo do estudante (DB-039).
- **Definição de Pronto (DoD)**: Serviço testado unitariamente e integrado ao fluxo de avaliação prática.
- **Observações Técnicas**: Conecta as entregas de oficina (EPIC-04) com a gamificação (EPIC-09).

---

### [BE-048] Middleware / Serviço de Registro de Ações Sensíveis no Log de Auditoria
- **ID**: `BE-048`
- **Título**: Middleware / Serviço de Registro de Ações Sensíveis no Log de Auditoria
- **Área**: Back-end
- **Epic**: EPIC-10: Relatórios, Governança de Dados & Qualidade
- **Lote / Sprint**: Lote 5 (S5)
- **Sequência na Squad**: ⬅️ Anterior: `BE-047` | ➡️ Próximo: `BE-049`
- **Dependências Diretas**: `BE-009, BE-019, BE-027, BE-039, BE-045, DB-009`
- **Prioridade**: P1 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Rastrear automaticamente todas as operações críticas (alteração de notas, status de matrícula, leitura/escrita de notas pedagógicas e resolução de alertas).
- **Descrição**: Implementar AuditService em Python que grava em audit_logs (DB-009): user_id, action, entity, entity_id, old_values (mascarando senhas/segredos), new_values, ip_address e timestamp. Disponibilizar GET /api/v1/admin/audit-logs restrito a ADMIN e COORDINATOR.
- **História de Usuário**: Como Coordenador ou Auditor, quero consultar o histórico de alterações sensíveis sem que dados pessoais desnecessários vazem em logs.
- **Critérios de Aceitação**:
- Grava auditoria automática nas rotas de notas, matrículas, alertas e observações restritas.
- Sanitiza campos sensíveis (password, tokens) antes de persistir.
- Endpoint GET /api/v1/admin/audit-logs paginado e filtrado por entidade e período.
- **Definição de Pronto (DoD)**: Auditoria ativa e verificada por testes de integração pytest.
- **Observações Técnicas**: Atende aos requisitos de segurança, logs e auditoria (seções 8 e 14).

---

### [BE-049] Exportação de Relatórios de Desempenho em Formato CSV / PDF com Python
- **ID**: `BE-049`
- **Título**: Exportação de Relatórios de Desempenho em Formato CSV / PDF com Python
- **Área**: Back-end
- **Epic**: EPIC-10: Relatórios, Governança de Dados & Qualidade
- **Lote / Sprint**: Lote 5 (S5)
- **Sequência na Squad**: ⬅️ Anterior: `BE-048` | ➡️ Próximo: `BE-050`
- **Dependências Diretas**: `BE-031, DB-036, DB-047`
- **Prioridade**: P1 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Disponibilizar endpoint GET /api/v1/reports/performance para exportação de relatórios consolidados de turma, notas, frequência e evolução por módulo.
- **Descrição**: Permitir que professores e coordenadores exportem dados consolidados da turma (filtrando por class_id, subject_id, module_id e format='csv'|'json') utilizando o módulo nativo csv do Python e StreamingResponse. Configura headers Content-Disposition e Content-Type adequados.
- **História de Usuário**: Como Coordenador ou Professor, quero exportar o relatório consolidado da turma em CSV para apresentar no conselho de classe.
- **Critérios de Aceitação**:
- Rota: GET /api/v1/reports/performance?class_id=...&format=csv.
- Não inclui observações confidenciais privadas no relatório geral exportado.
- StreamingResponse eficiente utilizando os índices de DB-047 e a view DB-036.
- **Definição de Pronto (DoD)**: Exportação funcionando e integrada à central de relatórios no frontend (FE-048).
- **Observações Técnicas**: Codificação UTF-8 com BOM no CSV (utf-8-sig) para abrir acentuação perfeitamente no Excel.

---

### [BE-050] Documentação OpenAPI/Swagger Nativa do FastAPI e Contrato Final Integrado
- **ID**: `BE-050`
- **Título**: Documentação OpenAPI/Swagger Nativa do FastAPI e Contrato Final Integrado
- **Área**: Back-end
- **Epic**: EPIC-10: Relatórios, Governança de Dados & Qualidade
- **Lote / Sprint**: Lote 5 (S5)
- **Sequência na Squad**: ⬅️ Anterior: `BE-049` | ➡️ Próximo: `Marco Final Concluído (100%)`
- **Dependências Diretas**: `BE-001, BE-010, BE-020, BE-030, BE-040, BE-048, BE-049, DB-050`
- **Prioridade**: P0 | **Estimativa**: 2 SP | **Tipo**: documentacao
- **Objetivo**: Consolidar e publicar a documentação interativa OpenAPI 3.0 (/docs e /redoc) de todos os 50 cards de back-end em Python e validar o contrato final com o Front-end (FE-050) e Banco (DB-050).
- **Descrição**: Configurar metadados do FastAPI (title, version, description, tags_metadata), esquemas de segurança OAuth2 Bearer, descrições ricas em cada endpoint via docstrings e schemas Pydantic, e exportar o arquivo openapi.json automatizado para DOC-013.
- **História de Usuário**: Como Equipe de Desenvolvimento e Banca Avaliadora, queremos explorar e testar todas as rotas da API em uma interface Swagger completa e documentada.
- **Critérios de Aceitação**:
- Rota GET /docs exibe Swagger UI interativo com todas as rotas agrupadas por tags (Auth, Academic, Diary, PracticalTasks, Dashboard, Diagnostics, Communication, Gamification, Reports).
- Exporta especificação OpenAPI válida para docs/api/openapi.json (DOC-013).
- Todos os testes de back-end (Lotes 1 a 5) passando 100% no pytest.
- **Definição de Pronto (DoD)**: Camada de Back-end em Python 100% concluída, documentada no Swagger e integrada com DB-050, FE-050 e DOC-020.
- **Observações Técnicas**: Marco de encerramento (Card 50/50) da squad de Back-end em Python.

