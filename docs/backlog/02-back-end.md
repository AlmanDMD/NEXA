# ⚙️ Backlog de Back-end (API & Serviços) — Projeto NEXA
## 50 Cards Exclusivos e Encadeados de Engenharia de Back-end (`BE-001` a `BE-050`)

Este documento contém o planejamento completo e 100% interligado da API RESTful e regras de negócio do **Sistema Inteligente de Monitoramento do Desempenho Acadêmico — SENAI (NEXA)**, conectando cada serviço às tabelas do Banco de Dados (`DB-001`..`DB-050`) e servindo o Front-end (`FE-001`..`FE-050`).

---

### Resumo dos Lotes / Sprints de Implementação
- **Lote 1 / Sprint 1 (BE-001 a BE-010)**: Setup Node.js/TypeScript, Arquitetura em Camadas, Autenticação JWT + Refresh Token, RBAC e Auditoria.
- **Lote 2 / Sprint 2 (BE-011 a BE-020)**: APIs de Gestão Acadêmica SENAI (Cursos, Turmas, Disciplinas, Módulos, Matriz de Competências e Matrículas em Lote).
- **Lote 3 / Sprint 3 (BE-021 a BE-030)**: APIs de Diário de Classe, Chamada em Lote, Tarefas Práticas de Oficina, Rubricas e Motor de Cálculo de Médias.
- **Lote 4 / Sprint 4 (BE-031 a BE-040)**: APIs de Autoavaliação, Cruzamento Percepção vs. Evidência, Motor de Alertas Precoces e Endpoints de Dashboard 360°.
- **Lote 5 / Sprint 5 (BE-041 a BE-050)**: Mural de Avisos, Canal Confidencial de Ajuda, Criptografia AES-256-GCM de Notas Pedagógicas, Gamificação, Relatórios PDF/CSV e Suite E2E Final.

---

### Tabela Geral Encadeada (50 Cards)

| ID | Título | Epic | Prioridade | Estimativa | Lote / Sprint | Dependências |
|---|---|---|---|---|---|---|
| `BE-001` | Configurar Boilerplate TypeScript com Fastify e Estrutura em Camadas | EPIC-01 | P0 | 3 SP | Lote 1 (S1) | `Nenhuma` |
| `BE-002` | Implementar Middleware Global de Tratamento de Erros e Logs Estruturados | EPIC-01 | P0 | 2 SP | Lote 1 (S1) | `BE-001` |
| `BE-003` | Configurar Schemas de Validação de Requisição com Zod | EPIC-01 | P0 | 2 SP | Lote 1 (S1) | `BE-001, BE-002` |
| `BE-004` | Implementar Serviço de Hash de Senhas e Verificação Criptográfica | EPIC-01 | P0 | 2 SP | Lote 1 (S1) | `BE-001` |
| `BE-005` | Endpoint de Registro e Login com Emissão de Token JWT e HttpOnly Cookie | EPIC-01 | P0 | 5 SP | Lote 1 (S1) | `BE-003, BE-004, DB-006, DB-008` |
| `BE-006` | Endpoint de Renovação de Sessão via Refresh Token Seguro | EPIC-01 | P0 | 3 SP | Lote 1 (S1) | `BE-005, DB-008` |
| `BE-007` | Endpoint de Logout com Invalidação de Sessão no Banco | EPIC-01 | P0 | 2 SP | Lote 1 (S1) | `BE-005, DB-008` |
| `BE-008` | Middleware de Autenticação JWT e Extração de Usuário no Request Context | EPIC-01 | P0 | 3 SP | Lote 1 (S1) | `BE-005` |
| `BE-009` | Middleware de Controle de Acesso por Papel (RBAC: Admin, Coord, Teacher, Student) | EPIC-01 | P0 | 3 SP | Lote 1 (S1) | `BE-008, DB-005` |
| `BE-010` | Endpoint de Consulta do Usuário Autenticado Atual | EPIC-01 | P0 | 2 SP | Lote 1 (S1) | `BE-008, DB-007` |
| `BE-011` | Endpoints CRUD de Cursos Técnicos SENAI | EPIC-02 | P0 | 3 SP | Lote 2 (S2) | `BE-009, DB-011` |
| `BE-012` | Endpoints CRUD de Turmas Acadêmicas e Períodos Letivos | EPIC-02 | P0 | 3 SP | Lote 2 (S2) | `BE-011, DB-012` |
| `BE-013` | Endpoints CRUD de Disciplinas do Currículo | EPIC-02 | P0 | 3 SP | Lote 2 (S2) | `BE-011, DB-013` |
| `BE-014` | Endpoints para Módulos de Aprendizagem Prática (Tornearia, Metrologia) | EPIC-02 | P0 | 3 SP | Lote 2 (S2) | `BE-013, DB-014` |
| `BE-015` | Endpoints para Gestão de Competências e Habilidades Técnicas | EPIC-04 | P0 | 3 SP | Lote 2 (S2) | `BE-014, DB-015, DB-016` |
| `BE-016` | Endpoint para Matrícula de Estudante em Turma com Validação de Vagas | EPIC-02 | P0 | 3 SP | Lote 2 (S2) | `BE-012, DB-017` |
| `BE-017` | Endpoint para Consulta de Alunos Matriculados por Turma | EPIC-02 | P0 | 2 SP | Lote 2 (S2) | `BE-016, DB-017` |
| `BE-018` | Endpoint para Alocação de Docente em Disciplina/Turma | EPIC-02 | P0 | 2 SP | Lote 2 (S2) | `BE-012, BE-013, DB-018` |
| `BE-019` | Endpoint para Alteração de Status da Matrícula (Ativo, Trancado, Concluído) | EPIC-02 | P1 | 2 SP | Lote 2 (S2) | `BE-016, DB-009, DB-017` |
| `BE-020` | Testes de Integração da Camada de Gestão Acadêmica | EPIC-02 | P0 | 5 SP | Lote 2 (S2) | `BE-011, BE-012, BE-013, BE-014, BE-015, BE-016, BE-017, BE-018, BE-019, DB-020` |
| `BE-021` | Endpoint para Registro de Aula Ministrada e Conteúdo Prático | EPIC-03 | P0 | 3 SP | Lote 3 (S3) | `BE-009, BE-018, DB-021` |
| `BE-022` | Endpoint de Chamada Rápida em Lote (Presença e Faltas) | EPIC-03 | P0 | 5 SP | Lote 3 (S3) | `BE-017, BE-021, DB-022` |
| `BE-023` | Endpoint de Consulta de Frequência Consolidada do Aluno | EPIC-03 | P0 | 3 SP | Lote 3 (S3) | `BE-009, BE-022, DB-022, DB-037` |
| `BE-024` | Endpoint para Criação de Atividade Prática com Critérios de Tolerância | EPIC-04 | P0 | 3 SP | Lote 3 (S3) | `BE-014, BE-015, DB-023, DB-024, DB-025` |
| `BE-025` | Endpoint para Registro de Conclusão de Tarefa Prática pelo Docente | EPIC-04 | P0 | 5 SP | Lote 3 (S3) | `BE-024, DB-025, DB-026, DB-033` |
| `BE-026` | Endpoint para Listagem de Tarefas Práticas Pendentes de um Aluno | EPIC-04 | P0 | 3 SP | Lote 3 (S3) | `BE-024, BE-025, DB-025` |
| `BE-027` | Endpoint para Lançamento de Notas de Avaliações Formativas | EPIC-03 | P0 | 3 SP | Lote 3 (S3) | `BE-017, DB-009, DB-027, DB-028` |
| `BE-028` | Endpoint para Fechamento de Médias e Cálculo Ponderado Automático | EPIC-03 | P1 | 5 SP | Lote 3 (S3) | `BE-025, BE-027, DB-014, DB-028` |
| `BE-029` | Middleware de Bloqueio de Alteração em Período Letivo Encerrado | EPIC-03 | P1 | 3 SP | Lote 3 (S3) | `BE-012, BE-022, BE-027, DB-029` |
| `BE-030` | Testes Automatizados para Cálculos de Médias e Frequência | EPIC-03 | P0 | 3 SP | Lote 3 (S3) | `BE-021, BE-022, BE-023, BE-024, BE-025, BE-026, BE-027, BE-028, BE-029, DB-030` |
| `BE-031` | Endpoint de Dashboard do Professor com Métricas Consolidadas da Turma | EPIC-05 | P0 | 5 SP | Lote 4 (S4) | `BE-028, DB-036, DB-037` |
| `BE-032` | Motor de Regras para Identificação Precoce de Risco Acadêmico (Alerta) | EPIC-05 | P0 | 5 SP | Lote 4 (S4) | `BE-022, BE-025, BE-028, DB-034, DB-036` |
| `BE-033` | Endpoint para Listagem de Alunos em Risco com Justificativa Explicável | EPIC-05 | P0 | 3 SP | Lote 4 (S4) | `BE-032, DB-034` |
| `BE-034` | Endpoint do Portal do Aluno com Progresso e Linha do Tempo | EPIC-06 | P0 | 5 SP | Lote 4 (S4) | `BE-008, BE-023, BE-026, DB-036, DB-039` |
| `BE-035` | Endpoint para Cadastro de Questionário de Autoavaliação de Competências | EPIC-07 | P1 | 3 SP | Lote 4 (S4) | `BE-014, BE-015, DB-031` |
| `BE-036` | Endpoint para Submissão de Respostas de Autoavaliação pelo Aluno | EPIC-07 | P1 | 3 SP | Lote 4 (S4) | `BE-035, DB-032` |
| `BE-037` | Algoritmo de Cruzamento: Autoavaliação vs Avaliação Prática do Docente | EPIC-07 | P1 | 5 SP | Lote 4 (S4) | `BE-025, BE-032, BE-036, DB-033, DB-035, DB-038` |
| `BE-038` | Endpoint de Consulta de Discrepâncias de Aprendizagem para Apoio Pedagógico | EPIC-07 | P1 | 3 SP | Lote 4 (S4) | `BE-037, DB-035, DB-038` |
| `BE-039` | Endpoint para Resolução e Histórico de Alertas Acadêmicos | EPIC-05 | P1 | 2 SP | Lote 4 (S4) | `BE-032, BE-033, DB-009, DB-034` |
| `BE-040` | Testes de Carga e Performance nas Rotas de Dashboard | EPIC-05 | P1 | 3 SP | Lote 4 (S4) | `BE-031, BE-032, BE-033, BE-034, BE-035, BE-036, BE-037, BE-038, BE-039, DB-040` |
| `BE-041` | Endpoint para Publicação de Avisos no Mural da Turma | EPIC-08 | P1 | 2 SP | Lote 5 (S5) | `BE-009, BE-018, DB-041` |
| `BE-042` | Endpoint para Consulta de Mural com Filtro de Turma e Disciplina | EPIC-08 | P1 | 2 SP | Lote 5 (S5) | `BE-041, DB-041` |
| `BE-043` | Endpoint para Abertura de Solicitação de Apoio Confidencial pelo Aluno | EPIC-08 | P0 | 3 SP | Lote 5 (S5) | `BE-009, BE-018, DB-042, DB-044` |
| `BE-044` | Endpoint para Atendimento e Encerramento de Pedidos de Ajuda | EPIC-08 | P0 | 3 SP | Lote 5 (S5) | `BE-043, DB-042, DB-044` |
| `BE-045` | Endpoint para Registro de Observações Pedagógicas com Acesso Restrito | EPIC-08 | P0 | 3 SP | Lote 5 (S5) | `BE-009, DB-009, DB-043` |
| `BE-046` | Endpoint de Conquistas e Badges Desbloqueadas pelo Estudante | EPIC-09 | P2 | 2 SP | Lote 5 (S5) | `BE-008, DB-045, DB-046` |
| `BE-047` | Serviço de Cálculo de Níveis de Habilidade Baseado em Entregas Práticas | EPIC-09 | P2 | 3 SP | Lote 5 (S5) | `BE-025, BE-046, DB-039, DB-045, DB-046` |
| `BE-048` | Middleware de Registro de Ações Sensíveis no Log de Auditoria | EPIC-10 | P1 | 3 SP | Lote 5 (S5) | `BE-009, BE-019, BE-027, BE-039, BE-045, DB-009` |
| `BE-049` | Exportação de Relatórios de Desempenho em Formato CSV / PDF | EPIC-10 | P1 | 3 SP | Lote 5 (S5) | `BE-031, DB-036, DB-047` |
| `BE-050` | Geração Automatizada de Documentação Interativa com Swagger/OpenAPI | EPIC-10 | P0 | 2 SP | Lote 5 (S5) | `BE-001, BE-010, BE-020, BE-030, BE-040, BE-048, BE-049, DB-050` |

---

## Detalhamento Completo e Encadeado dos 50 Cards

### [BE-001] Configurar Boilerplate TypeScript com Fastify e Estrutura em Camadas
- **ID**: `BE-001`
- **Título**: Configurar Boilerplate TypeScript com Fastify e Estrutura em Camadas
- **Área**: Back-end
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `Início da Trilha` | ➡️ Próximo: `BE-002`
- **Dependências Diretas**: `Nenhuma`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: infraestrutura
- **Objetivo**: Estruturar o projeto backend em Node.js com TypeScript, servidor Fastify e arquitetura em camadas desacopladas (Controllers, Services, Repositories).
- **Descrição**: Configurar tsconfig.json rigoroso, setup do Fastify com suporte a JSON, CORS parametrizado via .env, graceful shutdown e injeção de dependências simplificada.
- **História de Usuário**: Como Desenvolvedor Back-end, quero uma base limpa e padronizada, para implementar novos endpoints com consistência arquitetural.
- **Critérios de Aceitação**:
- Servidor inicializa na porta configurada via .env.
- Estrutura de pastas: src/controllers, src/services, src/repositories, src/routes, src/middlewares, src/schemas.
- Endpoint GET /health retornando status: ok e timestamp.
- **Definição de Pronto (DoD)**: npm run dev inicia o servidor Fastify e responde ao healthcheck.
- **Observações Técnicas**: Fastify foi escolhido por performance superior em relação ao Express e suporte nativo a schema serialization.

---

### [BE-002] Implementar Middleware Global de Tratamento de Erros e Logs Estruturados
- **ID**: `BE-002`
- **Título**: Implementar Middleware Global de Tratamento de Erros e Logs Estruturados
- **Área**: Back-end
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `BE-001` | ➡️ Próximo: `BE-003`
- **Dependências Diretas**: `BE-001`
- **Prioridade**: P0 | **Estimativa**: 2 SP | **Tipo**: feature
- **Objetivo**: Interceptar e tratar centralizadamente todas as exceções da API, retornando respostas padronizadas sem vazar detalhes de infraestrutura.
- **Descrição**: Criar classe base AppError (com statusCode e message), middleware de setErrorHandler no Fastify capturando erros do Zod, erros do Prisma (P2002, P2025) e erros 500 inesperados com log estruturado usando Pino.
- **História de Usuário**: Como Desenvolvedor Front-end, quero respostas de erro previsíveis e padronizadas (status, code, message, details), para exibir mensagens claras ao usuário.
- **Critérios de Aceitação**:
- Respostas de erro seguem o formato: { success: false, statusCode, error, message, details?: [] }.
- Erros de validação Zod retornam HTTP 400 com lista de campos inválidos.
- Erros não tratados logados internamente e retornam HTTP 500 amigável.
- **Definição de Pronto (DoD)**: Testes unitários cobrindo cenários de erro 400, 401, 403, 404 e 500 passando.
- **Observações Técnicas**: Nunca expor stack traces ou queries SQL cruas em respostas de produção.

---

### [BE-003] Configurar Schemas de Validação de Requisição com Zod
- **ID**: `BE-003`
- **Título**: Configurar Schemas de Validação de Requisição com Zod
- **Área**: Back-end
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `BE-002` | ➡️ Próximo: `BE-004`
- **Dependências Diretas**: `BE-001, BE-002`
- **Prioridade**: P0 | **Estimativa**: 2 SP | **Tipo**: feature
- **Objetivo**: Garantir validação estrita de tipos e regras de entrada (body, query params, path params) em todas as rotas da API.
- **Descrição**: Configurar biblioteca Zod e criar helper ou middleware validateRequest(schema) capaz de validar body, params e query de forma síncrona/assíncrona antes do controller ser acionado.
- **História de Usuário**: Como Engenheiro de Software, quero validar todas as entradas com Zod, para rejeitar payloads maliciosos ou incompletos antes de tocar o banco de dados.
- **Critérios de Aceitação**:
- Validação automática de payloads rejeitando propriedades extras quando configurado.
- Mensagens de erro em português para validações comuns (ex: e-mail inválido, senha muito curta).
- Tipos TypeScript inferidos diretamente dos schemas Zod (z.infer).
- **Definição de Pronto (DoD)**: Helper de validação funcionando e tipado corretamente.
- **Observações Técnicas**: Facilita documentação automática via Zod-to-OpenAPI mais adiante.

---

### [BE-004] Implementar Serviço de Hash de Senhas e Verificação Criptográfica
- **ID**: `BE-004`
- **Título**: Implementar Serviço de Hash de Senhas e Verificação Criptográfica
- **Área**: Back-end
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `BE-003` | ➡️ Próximo: `BE-005`
- **Dependências Diretas**: `BE-001`
- **Prioridade**: P0 | **Estimativa**: 2 SP | **Tipo**: feature
- **Objetivo**: Proteger as senhas dos usuários utilizando algoritmo moderno de hash com salt aleatório.
- **Descrição**: Implementar AuthService.hashPassword(password) e AuthService.comparePassword(password, hash) utilizando bcryptjs ou argon2 com fator de custo calibrado (salt rounds = 12).
- **História de Usuário**: Como Usuário do Sistema, quero que minha senha seja criptografada de forma segura, para que mesmo em caso de violação de dados ela não seja descoberta.
- **Critérios de Aceitação**:
- Nenhuma senha em texto puro é trafegada internamente além da validação.
- Comparação em tempo constante para evitar timing attacks.
- Testes unitários com senhas corretas e incorretas.
- **Definição de Pronto (DoD)**: Serviço com cobertura de testes unitários de 100%.
- **Observações Técnicas**: Utilizar bcryptjs ou argon2id, respeitando as recomendações da OWASP.

---

### [BE-005] Endpoint de Registro e Login com Emissão de Token JWT e HttpOnly Cookie
- **ID**: `BE-005`
- **Título**: Endpoint de Registro e Login com Emissão de Token JWT e HttpOnly Cookie
- **Área**: Back-end
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `BE-004` | ➡️ Próximo: `BE-006`
- **Dependências Diretas**: `BE-003, BE-004, DB-006, DB-008`
- **Prioridade**: P0 | **Estimativa**: 5 SP | **Tipo**: feature
- **Objetivo**: Disponibilizar endpoint de autenticação POST /api/v1/auth/login emitindo access token de curta duração e refresh token gravado em cookie seguro.
- **Descrição**: Validar credenciais recebidas (email e password). Em caso de sucesso, gerar Access Token JWT (vida útil de 15 minutos) e Refresh Token (vida útil de 7 dias gravado na tabela auth_sessions). Enviar Refresh Token via cookie com flags HttpOnly, Secure e SameSite=Strict.
- **História de Usuário**: Como Usuário, quero fazer login informando meu e-mail e senha, para acessar as funcionalidades autorizadas do meu perfil.
- **Critérios de Aceitação**:
- Rota: POST /api/v1/auth/login.
- Retorno HTTP 200 com { user: { id, email, role, profile }, accessToken }.
- Cookie refreshToken gravado com HttpOnly.
- Retorno HTTP 401 com mensagem genérica 'Credenciais inválidas' para e-mail inexistente ou senha incorreta.
- **Definição de Pronto (DoD)**: Endpoint testado ponta a ponta com Postman/Thunder Client e testes de integração.
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
- **Objetivo**: Permitir que clientes com token expirado obtenham novo Access Token sem necessidade de novo login.
- **Descrição**: Endpoint POST /api/v1/auth/refresh que lê o cookie HttpOnly refreshToken, busca o hash no banco, valida se não está expirado ou revogado, gera novo par de tokens (token rotation) e invalida o refresh token anterior.
- **História de Usuário**: Como Usuário, quero que minha sessão permaneça ativa enquanto uso o sistema, sem que precise digitar minha senha a cada 15 minutos.
- **Critérios de Aceitação**:
- Rota: POST /api/v1/auth/refresh.
- Sucesso HTTP 200 com novo accessToken e novo cookie de refresh.
- Retorno HTTP 401 se token for inválido, revogado ou expirado.
- Detecção de reúso de refresh token revogado (ação de segurança com revogação em cadeia).
- **Definição de Pronto (DoD)**: Fluxo de renovação e rotação de tokens testado e validado.
- **Observações Técnicas**: Refresh token rotation é fundamental para mitigar roubo de tokens.

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
- **Objetivo**: Encerrar formalmente a sessão do usuário no servidor e limpar os cookies do cliente.
- **Descrição**: Endpoint POST /api/v1/auth/logout que recebe o refresh token, marca is_revoked = true na tabela auth_sessions e limpa o cookie com maxAge: 0.
- **História de Usuário**: Como Usuário, quero fazer logout do sistema, garantindo que ninguém possa usar meu acesso no computador da oficina.
- **Critérios de Aceitação**:
- Rota: POST /api/v1/auth/logout.
- Retorno HTTP 200 com { message: 'Sessão encerrada com sucesso' }.
- Cookie refreshToken limpo no navegador.
- Sessão invalidada no banco.
- **Definição de Pronto (DoD)**: Logout testado e confirmação de que o refresh token anterior é rejeitado após logout.
- **Observações Técnicas**: Essencial para computadores compartilhados em laboratórios SENAI.

---

### [BE-008] Middleware de Autenticação JWT e Extração de Usuário no Request Context
- **ID**: `BE-008`
- **Título**: Middleware de Autenticação JWT e Extração de Usuário no Request Context
- **Área**: Back-end
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `BE-007` | ➡️ Próximo: `BE-009`
- **Dependências Diretas**: `BE-005`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Interceptar requisições em rotas protegidas, validar o header Authorization Bearer <token> e injetar os dados do usuário autenticado no request.
- **Descrição**: Implementar middleware authenticateUser que verifica assinatura do JWT com a chave secreta, checa expiração e anexa request.user = { id, email, role } no contexto da requisição.
- **História de Usuário**: Como Desenvolvedor de Rotas, quero ter request.user disponível nos controllers protegidos, para identificar quem está executando a ação.
- **Critérios de Aceitação**:
- Bloqueia requisições sem header Authorization retornando HTTP 401.
- Bloqueia tokens com assinatura inválida ou expirados com HTTP 401.
- Anexa usuário tipado no contexto do Fastify.
- **Definição de Pronto (DoD)**: Middleware testado e aplicado em rota de exemplo com sucesso.
- **Observações Técnicas**: Usar fastify.decorateRequest('user', null) para tipagem estrita no TypeScript.

---

### [BE-009] Middleware de Controle de Acesso por Papel (RBAC: Admin, Coord, Teacher, Student)
- **ID**: `BE-009`
- **Título**: Middleware de Controle de Acesso por Papel (RBAC: Admin, Coord, Teacher, Student)
- **Área**: Back-end
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `BE-008` | ➡️ Próximo: `BE-010`
- **Dependências Diretas**: `BE-008, DB-005`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Restringir o acesso a rotas específicas com base no papel institucional do usuário.
- **Descrição**: Criar middleware autorizador requireRole(allowedRoles: Role[]) que checa request.user.role e retorna HTTP 403 Forbidden caso o usuário autenticado não possua um dos papéis permitidos.
- **História de Usuário**: Como Coordenador Pedagógico, quero que estudantes não possam acessar endpoints de lançamento de notas ou criação de turmas, para manter a segurança do sistema.
- **Critérios de Aceitação**:
- Usuário autenticado sem o papel exigido recebe HTTP 403 com mensagem clara.
- Suporte a múltiplos papéis (ex: requireRole(['ADMIN', 'COORDINATOR'])).
- Teste cobrindo Aluno tentando acessar rota de Professor.
- **Definição de Pronto (DoD)**: Suíte de testes de autorização com perfis distintos passando.
- **Observações Técnicas**: Permissões contextuais (ex: professor daquela turma específica) serão complementadas nos services.

---

### [BE-010] Endpoint de Consulta do Usuário Autenticado Atual
- **ID**: `BE-010`
- **Título**: Endpoint de Consulta do Usuário Autenticado Atual
- **Área**: Back-end
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `BE-009` | ➡️ Próximo: `BE-011`
- **Dependências Diretas**: `BE-008, DB-007`
- **Prioridade**: P0 | **Estimativa**: 2 SP | **Tipo**: feature
- **Objetivo**: Permitir que a aplicação cliente obtenha os dados de perfil completos do usuário logado na inicialização.
- **Descrição**: Endpoint GET /api/v1/auth/me protegido por autenticação. Retorna dados cadastrais do usuário (id, email, role, profile, permissions) sem expor senhas ou tokens internos.
- **História de Usuário**: Como Usuário do Front-end, quero carregar meus dados de perfil ao abrir a página, para que o sistema mostre meu nome e menu personalizado.
- **Critérios de Aceitação**:
- Rota: GET /api/v1/auth/me.
- Retorno HTTP 200 com perfil completo e matrícula SENAI.
- Retorno HTTP 401 se não autenticado.
- Não expõe password_hash.
- **Definição de Pronto (DoD)**: Endpoint funcional e integrado com schema Prisma.
- **Observações Técnicas**: Adicionar cabeçalho Cache-Control: no-store para evitar cache de dados sensíveis.

---

### [BE-011] Endpoints CRUD de Cursos Técnicos SENAI
- **ID**: `BE-011`
- **Título**: Endpoints CRUD de Cursos Técnicos SENAI
- **Área**: Back-end
- **Epic**: EPIC-02: Gestão Acadêmica & Estrutura SENAI
- **Lote / Sprint**: Lote 2 (S2)
- **Sequência na Squad**: ⬅️ Anterior: `BE-010` | ➡️ Próximo: `BE-012`
- **Dependências Diretas**: `BE-009, DB-011`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Disponibilizar endpoints administrativos para cadastro, listagem, atualização e desativação de cursos técnicos.
- **Descrição**: Criar rotas: GET /api/v1/courses (com paginação e busca por nome), POST /api/v1/courses (validação Zod do código e carga horária), GET /api/v1/courses/:id e PUT /api/v1/courses/:id. Acesso restrito a ADMIN e COORDINATOR.
- **História de Usuário**: Como Coordenador, quero gerenciar os cursos técnicos da unidade, para organizar a oferta formativa.
- **Critérios de Aceitação**:
- GET /api/v1/courses retorna lista paginada { data, meta: { total, page, limit } }.
- POST valida se código do curso já existe (rejeita com HTTP 409 se duplicado).
- Exclusão lógica (soft delete via is_active = false).
- **Definição de Pronto (DoD)**: Endpoints implementados com validação Zod e testes de integração.
- **Observações Técnicas**: Impedir desativação de curso caso existam turmas com status ACTIVE vinculadas.

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
- **Objetivo**: Gerenciar as turmas semestrais, turnos e capacidades de alunos.
- **Descrição**: Criar rotas: GET /api/v1/classes (com filtros por curso, período letivo e turno), POST /api/v1/classes (criação com validação de datas), GET /api/v1/classes/:id (detalhes com curso e quantidade de matriculados) e PATCH /api/v1/classes/:id/status.
- **História de Usuário**: Como Coordenador, quero criar e listar turmas, para alocar os alunos matriculados no semestre.
- **Critérios de Aceitação**:
- Criação de turma vinculada a curso existente (HTTP 404 se curso inválido).
- Validação: start_date anterior a end_date.
- Retorno de quantidade atual de matriculados vs max_students.
- **Definição de Pronto (DoD)**: Endpoints funcionais com validação Zod e autorização para coordenadores.
- **Observações Técnicas**: Permitir que professores consultem turmas onde lecionam sem precisar de permissão global.

---

### [BE-013] Endpoints CRUD de Disciplinas do Currículo
- **ID**: `BE-013`
- **Título**: Endpoints CRUD de Disciplinas do Currículo
- **Área**: Back-end
- **Epic**: EPIC-02: Gestão Acadêmica & Estrutura SENAI
- **Lote / Sprint**: Lote 2 (S2)
- **Sequência na Squad**: ⬅️ Anterior: `BE-012` | ➡️ Próximo: `BE-014`
- **Dependências Diretas**: `BE-011, DB-013`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Disponibilizar endpoints para gestão das unidades curriculares da matriz técnica.
- **Descrição**: Rotas: GET /api/v1/subjects (filtro por courseId), POST /api/v1/subjects, GET /api/v1/subjects/:id e PUT /api/v1/subjects/:id. Suporte a ementa técnica e carga horária.
- **História de Usuário**: Como Coordenador Pedagógico, quero cadastrar disciplinas vinculadas aos cursos, para associar os módulos de oficina.
- **Critérios de Aceitação**:
- POST exige nome, código, courseId e carga horária positiva.
- Listagem permite filtrar apenas disciplinas ativas.
- HTTP 400 se carga horária for menor ou igual a zero.
- **Definição de Pronto (DoD)**: Rotas implementadas e documentadas com Zod schema.
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
- **Descrição**: Rotas: GET /api/v1/subjects/:subjectId/modules (ordenados por order_index) e POST /api/v1/modules (criação de módulo prático com horas de oficina e nota de corte).
- **História de Usuário**: Como Professor de Prática, quero consultar os módulos da disciplina na ordem didática correta, para registrar as atividades de bancada.
- **Critérios de Aceitação**:
- Módulos retornam ordenados por order_index ascendente.
- Validação de passing_score entre 0.00 e 10.00.
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
- **Descrição**: Rotas: GET /api/v1/competencies (busca e filtro por categoria), POST /api/v1/competencies, e POST /api/v1/modules/:id/competencies (vinculando competência a módulo com peso e nível).
- **História de Usuário**: Como Professor, quero associar competências específicas aos módulos práticos, para avaliar se o aluno atingiu o critério de tolerância ou operação de máquina.
- **Critérios de Aceitação**:
- Validação de código único de competência.
- Vinculação módulo-competência com nível requerido entre 1 e 5.
- Consulta com detalhes de competências agregadas por módulo.
- **Definição de Pronto (DoD)**: Rotas criadas com validação de payload no Zod.
- **Observações Técnicas**: Fundamental para renderizar o gráfico de teia de aranha (radar) no frontend.

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
- **Objetivo**: Processar a matrícula de um estudante em uma turma garantindo limites de vagas e consistência de dados.
- **Descrição**: Endpoint POST /api/v1/enrollments recebendo studentId e classId. Executa transação verificando se a turma está ativa, se o limite max_students não foi atingido e se o aluno já não está matriculado na mesma turma.
- **História de Usuário**: Como Secretaria, quero matricular um aluno em uma turma, garantindo que o limite de capacidade da oficina não seja ultrapassado.
- **Critérios de Aceitação**:
- Rota: POST /api/v1/enrollments.
- HTTP 201 Created se houver vaga e aluno for válido.
- HTTP 409 Conflict se aluno já estiver matriculado.
- HTTP 422 Unprocessable Entity se turma estiver lotada (max_students atingido).
- **Definição de Pronto (DoD)**: Endpoint implementado com transação atômica Prisma ($transaction) e teste de concorrência.
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
- **Descrição**: Endpoint GET /api/v1/classes/:id/students que retorna lista ordenada alfabeticamente contendo: id do aluno, nome completo, número de matrícula, status da matrícula, frequência acumulada e nota parcial.
- **História de Usuário**: Como Professor, quero consultar a lista dos meus alunos de uma turma, para realizar a chamada de presença e registrar tarefas.
- **Critérios de Aceitação**:
- Rota: GET /api/v1/classes/:id/students.
- Retorno HTTP 200 com array de estudantes e metadados da turma.
- Apenas professores alocados à turma ou coordenadores podem visualizar.
- **Definição de Pronto (DoD)**: Endpoint testado com retorno populado via seed.
- **Observações Técnicas**: Incluir dados do perfil (user_profiles) com join eficiente para evitar problema de N+1 queries.

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
- **Descrição**: Endpoint POST /api/v1/teacher-assignments recebendo teacherId, classId, subjectId e isMainTeacher. Valida se o usuário informado possui a role TEACHER.
- **História de Usuário**: Como Coordenador, quero associar o instrutor de usinagem à sua respectiva oficina e turma, para que ele visualize sua pauta de aulas.
- **Critérios de Aceitação**:
- Rota: POST /api/v1/teacher-assignments.
- HTTP 201 com atribuição criada.
- HTTP 400 se o usuário indicado não for um professor cadastrado.
- HTTP 409 se o professor já estiver atribuído a esta disciplina nesta turma.
- **Definição de Pronto (DoD)**: Endpoint funcional e documentado no Swagger.
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
- **Descrição**: Endpoint PATCH /api/v1/enrollments/:id/status recebendo o novo status (DROPPED, COMPLETED, SUSPENDED) e justificativa opcional. Registra a mudança no log de auditoria.
- **História de Usuário**: Como Secretaria, quero trancar ou concluir a matrícula de um estudante, para que as métricas da turma reflitam apenas alunos ativos.
- **Critérios de Aceitação**:
- Rota: PATCH /api/v1/enrollments/:id/status.
- HTTP 200 com status atualizado.
- Cria registro em audit_logs com valores antigos e novos.
- Alunos com status DROPPED deixam de impactar cálculos de faltas futuras.
- **Definição de Pronto (DoD)**: Endpoint testado com verificação de log de auditoria gerado.
- **Observações Técnicas**: Ação restrita a usuários com perfil ADMIN ou COORDINATOR.

---

### [BE-020] Testes de Integração da Camada de Gestão Acadêmica
- **ID**: `BE-020`
- **Título**: Testes de Integração da Camada de Gestão Acadêmica
- **Área**: Back-end
- **Epic**: EPIC-02: Gestão Acadêmica & Estrutura SENAI
- **Lote / Sprint**: Lote 2 (S2)
- **Sequência na Squad**: ⬅️ Anterior: `BE-019` | ➡️ Próximo: `BE-021`
- **Dependências Diretas**: `BE-011, BE-012, BE-013, BE-014, BE-015, BE-016, BE-017, BE-018, BE-019, DB-020`
- **Prioridade**: P0 | **Estimativa**: 5 SP | **Tipo**: teste
- **Objetivo**: Garantir a confiabilidade e robustez de todos os fluxos de gestão acadêmica implementados no Lote 2.
- **Descrição**: Criar suíte de testes de integração com Vitest/Supertest cobrindo: criação de curso, turma, disciplina, módulo prático, matrícula de estudante com validação de vagas e atribuição de docente.
- **História de Usuário**: Como Tech Lead, quero testes automatizados cobrindo os fluxos acadêmicos, para evitar regressões quando novas rotas forem adicionadas.
- **Critérios de Aceitação**:
- Suíte de testes executa com comando npm run test:integration.
- Cobertura mínima de 80% das rotas de gestão acadêmica.
- Testes executam contra banco de testes isolado e limpo após cada suíte.
- **Definição de Pronto (DoD)**: Testes passando 100% no terminal e configurados para CI.
- **Observações Técnicas**: Utilizar banco em memória ou container Docker dedicado com rollback de transações.

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
- **Objetivo**: Disponibilizar endpoints POST /api/v1/lessons e GET /api/v1/classes/:classId/lessons para criação e consulta do diário de bordo das aulas.
- **Descrição**: Permitir que o professor alocado à turma registre a aula do dia informando classId, subjectId, moduleId, lessonDate, workloadHours (1-8h), topicSummary e labEnvironment. Valida no servidor se o professor autenticado possui atribuição ativa (teacher_assignments) naquela turma e disciplina.
- **História de Usuário**: Como Professor, quero abrir o diário do dia informando o módulo e a oficina utilizada, para liberar o lançamento da chamada.
- **Critérios de Aceitação**:
- Rota: POST /api/v1/lessons (Status 201 Created) e GET /api/v1/classes/:classId/lessons (Status 200 OK).
- Rejeita com HTTP 403 se um professor tentar criar aula em turma que não leciona.
- Validação Zod de data e carga horária.
- **Definição de Pronto (DoD)**: Endpoints de diário funcionais, validados com Zod e consumíveis por FE-021.
- **Observações Técnicas**: Ao criar a aula, pode pré-inicializar lista de chamada ou permitir upsert no endpoint BE-022.

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
- **Objetivo**: Implementar endpoint POST /api/v1/lessons/:id/attendance que registra em uma única transação a presença de todos os alunos da turma.
- **Descrição**: Receber array { records: [{ studentId, status: 'PRESENT' | 'ABSENT' | 'LATE' | 'JUSTIFIED', absentHours, justificationNote }] }. Executar upsert transacional em attendance_records e recalcular imediatamente o attendance_rate do aluno na tabela enrollments.
- **História de Usuário**: Como Professor, quero salvar a chamada da turma inteira em 1 clique de forma muito mais rápida que preencher planilhas.
- **Critérios de Aceitação**:
- Rota: POST /api/v1/lessons/:id/attendance.
- Retorno HTTP 200 com resumo { totalProcessed, presentCount, absentCount, updatedEnrollments }.
- Rejeita com HTTP 400 se enviar studentId não matriculado na turma daquela aula.
- Recalcula attendance_rate no servidor (nunca confia em percentual enviado pelo cliente).
- **Definição de Pronto (DoD)**: Endpoint transacional testado e integrado à interface de chamada rápida (FE-022).
- **Observações Técnicas**: Se a frequência atualizada cair abaixo de 78%, aciona avaliação do motor de risco (BE-032).

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
- **Objetivo**: Expor endpoint GET /api/v1/students/:id/attendance com o extrato detalhado de presenças, faltas e margem restante até o limite de 75%.
- **Descrição**: Retornar o histórico de frequência do estudante agrupado por disciplina e módulo prático, utilizando a view vw_module_attendance_risk. Aplicar regra de autorização: um aluno só pode consultar o próprio ID (ou /me/attendance); professores e coordenadores podem consultar alunos de suas turmas.
- **História de Usuário**: Como Aluno ou Professor, quero consultar o percentual de presença por módulo e saber quantas horas ainda restam antes do limite de reprovação por faltas.
- **Critérios de Aceitação**:
- Rota: GET /api/v1/students/:id/attendance.
- HTTP 403 Forbidden se um estudante tentar consultar o ID de outro colega (prevenção IDOR).
- Retorna totalHours, attendedHours, absentHours, attendancePercentage e isCritical (<78%).
- **Definição de Pronto (DoD)**: Endpoint protegido contra IDOR e pronto para consumo em FE-023 e FE-037.
- **Observações Técnicas**: Regra estrita de isolamento de dados de cada aluno (seção 14).

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
- **Objetivo**: Permitir o cadastro e listagem de tarefas práticas de oficina (ex: Tornearia, Metrologia) juntamente com suas rubricas técnicas.
- **Descrição**: Implementar POST /api/v1/practical-tasks e GET /api/v1/modules/:moduleId/practical-tasks. Na criação, recebe os dados da tarefa e um array de critérios (task_criteria) vinculados às competências do módulo. Cria automaticamente registros iniciais PENDING em task_submissions para os alunos ativos da turma.
- **História de Usuário**: Como Instrutor SENAI, quero criar uma atividade prática definindo os critérios de medição e acabamento esperados na bancada.
- **Critérios de Aceitação**:
- Rota: POST /api/v1/practical-tasks (HTTP 201).
- Valida que todas as competências referenciadas nas rubricas existem no banco.
- Gera entregas pendentes para os alunos da turma em transação única.
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
- **Descrição**: Implementar POST /api/v1/tasks/:id/evaluations recebendo studentId, status ('EVALUATED'), avaliações por critério (criterionId, achievedLevel 1-5, technicalFeedback). Calcula a nota ponderada da tarefa no servidor, atualiza task_submissions e grava evidência em skill_evidences.
- **História de Usuário**: Como Professor de Oficina, quero avaliar a peça entregue pelo aluno na bancada em poucos toques, gerando a nota e a evidência da competência automaticamente.
- **Critérios de Aceitação**:
- Rota: POST /api/v1/tasks/:id/evaluations (HTTP 200/201).
- Calcula final_task_score no servidor a partir dos pesos de task_criteria.
- Alimenta automaticamente a tabela skill_evidences (DB-033) para o motor de diagnóstico.
- **Definição de Pronto (DoD)**: Fluxo de avaliação prática testado ponta a ponta e consumível por FE-025 e FE-026.
- **Observações Técnicas**: Evita que o cliente envie nota final manipulada; todo cálculo é feito pelo backend.

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
- **Objetivo**: Disponibilizar endpoint GET /api/v1/students/:id/pending-tasks listando atividades concluídas, pendentes e atrasadas.
- **Descrição**: Consultar task_submissions cruzando com practical_tasks e learning_modules. Marcar dinamicamente ou atualizar como LATE tarefas com status PENDING cujo due_date já expirou. Suporta filtros por status (PENDING, LATE, SUBMITTED, EVALUATED) e módulo.
- **História de Usuário**: Como Estudante, quero consultar todas as minhas atividades práticas pendentes e em atraso ordenadas por prazo de entrega.
- **Critérios de Aceitação**:
- Rota: GET /api/v1/students/:id/pending-tasks.
- Isolamento de segurança: estudante só acessa suas próprias pendências.
- Retorna contadores resumidos { pendingCount, lateCount, completedCount } e lista ordenada por due_date.
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
- **Objetivo**: Implementar endpoints para criar avaliações (POST /api/v1/assessments) e lançar notas em lote (POST /api/v1/assessments/:id/grades).
- **Descrição**: Permitir cadastro de provas e microavaliações teóricas/práticas e lançamento das notas (0.00 a 10.00) e notas de recuperação dos alunos da turma. Registra em audit_logs qualquer retificação de nota já existente.
- **História de Usuário**: Como Professor, quero lançar as notas das avaliações e recuperações de toda a turma em uma única tela tabular.
- **Critérios de Aceitação**:
- Rotas: POST /api/v1/assessments e POST /api/v1/assessments/:id/grades.
- Validação Zod impedindo notas < 0 ou > 10.
- Verifica se o estudante pertence à turma antes de gravar a nota.
- **Definição de Pronto (DoD)**: Endpoints implementados e integrados com FE-027.
- **Observações Técnicas**: Considera a maior nota entre grade_value e recovery_grade conforme regra pedagógica.

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
- **Objetivo**: Calcular no servidor as médias parciais e finais por módulo e disciplina combinando avaliações formativas e entregas práticas de oficina.
- **Descrição**: Implementar POST /api/v1/classes/:id/calculate-averages e GET /api/v1/classes/:id/grades-summary. Consolida notas de student_grades (ponderadas por weight) e task_submissions, atualizando final_grade em enrollments e identificando alunos abaixo da nota de corte (passing_score).
- **História de Usuário**: Como Professor ou Coordenador, quero que o sistema calcule automaticamente as médias ponderadas sem fórmulas manuais sujeitas a erro.
- **Critérios de Aceitação**:
- Rota: POST /api/v1/classes/:id/calculate-averages (HTTP 200).
- Retorna boletim consolidado por aluno e módulo com status (APPROVED, IN_RECOVERY, AT_RISK).
- Precisão numérica de duas casas decimais com arredondamento padronizado.
- **Definição de Pronto (DoD)**: Serviço de cálculo de médias validado e consumido por FE-028.
- **Observações Técnicas**: Aciona automaticamente atualização de indicadores de risco (BE-032).

---

### [BE-029] Middleware de Bloqueio de Alteração em Período Letivo Encerrado
- **ID**: `BE-029`
- **Título**: Middleware de Bloqueio de Alteração em Período Letivo Encerrado
- **Área**: Back-end
- **Epic**: EPIC-03: Diário de Classe: Notas & Frequência
- **Lote / Sprint**: Lote 3 (S3)
- **Sequência na Squad**: ⬅️ Anterior: `BE-028` | ➡️ Próximo: `BE-030`
- **Dependências Diretas**: `BE-012, BE-022, BE-027, DB-029`
- **Prioridade**: P1 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Bloquear requisições de mutação (POST/PUT/PATCH/DELETE) em aulas, frequências, tarefas e notas de turmas já encerradas.
- **Descrição**: Criar middleware ensureClassIsActive que verifica o status da turma alvo. Se status for COMPLETED ou ARCHIVED, rejeita imediatamente com HTTP 422 Unprocessable Entity ('Período letivo encerrado para esta turma'), exceto se reaberto formalmente por um ADMIN.
- **História de Usuário**: Como Coordenador, quero que o backend impeça alterações em diários de turmas já concluídas, exibindo mensagem clara ao professor.
- **Critérios de Aceitação**:
- Intercepta rotas de lançamento de notas, chamadas e avaliações práticas.
- Retorna HTTP 422 com código CLASS_PERIOD_CLOSED.
- Alinhado com a trigger de banco de dados (DB-029).
- **Definição de Pronto (DoD)**: Middleware aplicado e testado com turma em status COMPLETED.
- **Observações Técnicas**: Garante governança acadêmica em dupla camada (API + Banco).

---

### [BE-030] Testes Automatizados para Cálculos de Médias e Frequência
- **ID**: `BE-030`
- **Título**: Testes Automatizados para Cálculos de Médias e Frequência
- **Área**: Back-end
- **Epic**: EPIC-03: Diário de Classe: Notas & Frequência
- **Lote / Sprint**: Lote 3 (S3)
- **Sequência na Squad**: ⬅️ Anterior: `BE-029` | ➡️ Próximo: `BE-031`
- **Dependências Diretas**: `BE-021, BE-022, BE-023, BE-024, BE-025, BE-026, BE-027, BE-028, BE-029, DB-030`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: teste
- **Objetivo**: Validar com testes unitários e de integração todas as regras matemáticas de frequência (75%), rubricas práticas e médias ponderadas do Lote 3.
- **Descrição**: Criar suíte de testes Vitest cobrindo: cálculo de presença com faltas justificadas vs não justificadas, cálculo de rubricas de oficina, substituição por nota de recuperação, bloqueio de turma encerrada e prevenção de IDOR nas consultas de alunos.
- **História de Usuário**: Como Tech Lead, quero 100% de confiança nos cálculos de notas e faltas do sistema antes de construir os dashboards analíticos.
- **Critérios de Aceitação**:
- Testes unitários e de integração do Lote 3 passando sem erros.
- Casos de borda testados (nota 0, nota 10, 0 aulas dadas, 100% faltas).
- Verificação de segurança impedindo Aluno A de ver notas/faltas do Aluno B.
- **Definição de Pronto (DoD)**: Suíte de testes do Lote 3 verde no pipeline.
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
- **Objetivo**: Disponibilizar endpoint GET /api/v1/dashboard/teacher/classes/:id e GET /api/v1/students/:id/360 com visão híbrida da turma e ficha 360° do aluno.
- **Descrição**: Consultar vw_student_360_performance e agregar KPIs da turma: média geral da turma, taxa média de presença, percentual de entregas práticas concluídas no prazo, distribuição de desempenho por módulo (Desenho Técnico, Metrologia, Tornearia) e quantidade de alunos em atenção/risco.
- **História de Usuário**: Como Professor, quero abrir meu dashboard e enxergar imediatamente o panorama da turma em todos os módulos e a ficha completa de cada aluno.
- **Critérios de Aceitação**:
- Rotas: GET /api/v1/dashboard/teacher/classes/:id e GET /api/v1/students/:id/360.
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
- **Objetivo**: Implementar serviço transparente e explicável (RiskEngineService) que analisa frequência, notas e pendências práticas para gerar alertas precoces.
- **Descrição**: Implementar regras determinísticas e auditáveis: (1) Presença < 75% -> CRITICAL; Presença entre 75% e 78% -> HIGH; (2) >= 2 tarefas práticas atrasadas (LATE) -> MODERATE/HIGH; (3) Média parcial abaixo de passing_score -> HIGH. Grava/atualiza registros em academic_alerts com explainable_reason detalhado.
- **História de Usuário**: Como Professor e Coordenador, quero que o sistema identifique precocemente alunos que precisam de apoio pedagógico, explicando exatamente qual regra disparou o alerta.
- **Critérios de Aceitação**:
- Nenhuma decisão de caixa-preta: todo alerta possui explainable_reason legível e metric_snapshot JSON.
- Evita alertas duplicados abertos para o mesmo motivo e aluno.
- Apresenta o alerta como indicador de atenção pedagógica, nunca como reprovação automática.
- **Definição de Pronto (DoD)**: Motor de risco testado unitariamente com todos os graus (LOW, MODERATE, HIGH, CRITICAL).
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
- **Descrição**: Retornar lista paginada e filtrável (por classId, moduleId, riskLevel, alertCategory) de alertas ativos em academic_alerts, trazendo dados do aluno, motivo explicável, métricas atuais e sugestão de ação pedagógica (ex: 'Agendar mentoria prática no módulo de Metrologia').
- **História de Usuário**: Como Professor, quero filtrar os alunos em situação de risco na minha turma e ler o motivo detalhado para planejar uma intervenção oportuna.
- **Critérios de Aceitação**:
- Rota: GET /api/v1/dashboard/teacher/at-risk (HTTP 200).
- Ordenação padrão por severidade (CRITICAL -> HIGH -> MODERATE -> LOW).
- Restrito a professores das respectivas turmas e coordenadores.
- **Definição de Pronto (DoD)**: Endpoint funcional e integrado ao card de alunos em risco (FE-032).
- **Observações Técnicas**: Permite acionar criação rápida de observação pedagógica ou convite de mentoria.

---

### [BE-034] Endpoint do Portal do Aluno com Progresso e Linha do Tempo
- **ID**: `BE-034`
- **Título**: Endpoint do Portal do Aluno com Progresso e Linha do Tempo
- **Área**: Back-end
- **Epic**: EPIC-06: Portal de Autonomia do Aluno & Pendências
- **Lote / Sprint**: Lote 4 (S4)
- **Sequência na Squad**: ⬅️ Anterior: `BE-033` | ➡️ Próximo: `BE-035`
- **Dependências Diretas**: `BE-008, BE-023, BE-026, DB-036, DB-039`
- **Prioridade**: P0 | **Estimativa**: 5 SP | **Tipo**: feature
- **Objetivo**: Disponibilizar endpoint GET /api/v1/dashboard/student/me reunindo todas as informações privadas do próprio estudante autenticado.
- **Descrição**: Retornar para o aluno logado: resumo de frequência e médias por disciplina, progresso percentual em cada módulo prático, evolução de nível por competência técnica (dados para o gráfico radar), contadores de atividades (concluídas, pendentes, atrasadas) e linha do tempo (student_milestone_history).
- **História de Usuário**: Como Estudante, quero acessar meu painel privado e acompanhar minha evolução de habilidades, notas, frequência e marcos conquistados.
- **Critérios de Aceitação**:
- Rota: GET /api/v1/dashboard/student/me (HTTP 200).
- Usa exclusivamente o ID extraído do token JWT (request.user.id), impossibilitando acesso a dados de terceiros.
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
- **Descrição**: Implementar POST /api/v1/self-assessments/forms e GET /api/v1/classes/:classId/self-assessments/forms. Retorna para o formulário a lista de competências associadas ao módulo (module_competencies) com suas descrições e escala de 1 a 5.
- **História de Usuário**: Como Professor, quero disponibilizar o questionário de autoavaliação de um módulo para minha turma responder.
- **Critérios de Aceitação**:
- Criação valida se o módulo possui competências cadastradas.
- Valida janela de abertura e fechamento (opensAt < closesAt).
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
- **Descrição**: Implementar POST /api/v1/self-assessments/submit recebendo formId e array de respostas [{ competencyId, perceivedLevel (1-5), confidenceScore (1-5), difficultyNotes }]. Grava em student_self_assessments e dispara o algoritmo de cruzamento diagnóstico (BE-037).
- **História de Usuário**: Como Estudante, quero enviar minha autoavaliação das habilidades práticas do módulo e relatar dificuldades que tive nas máquinas.
- **Critérios de Aceitação**:
- Rota: POST /api/v1/self-assessments/submit (HTTP 201).
- Valida se o formulário está ativo e dentro do prazo.
- Impede submissão em nome de outro aluno (usa request.user.id).
- **Definição de Pronto (DoD)**: Submissão testada e integrada à tela de autoavaliação do aluno (FE-041).
- **Observações Técnicas**: Caso o aluno relate dificuldade alta (perceivedLevel <= 2), sugere abertura opcional de pedido de ajuda.

---

### [BE-037] Algoritmo de Cruzamento: Autoavaliação vs Avaliação Prática do Docente
- **ID**: `BE-037`
- **Título**: Algoritmo de Cruzamento: Autoavaliação vs Avaliação Prática do Docente
- **Área**: Back-end
- **Epic**: EPIC-07: Autoavaliação & Motor de Diagnóstico Explicável
- **Lote / Sprint**: Lote 4 (S4)
- **Sequência na Squad**: ⬅️ Anterior: `BE-036` | ➡️ Próximo: `BE-038`
- **Dependências Diretas**: `BE-025, BE-032, BE-036, DB-033, DB-035, DB-038`
- **Prioridade**: P1 | **Estimativa**: 5 SP | **Tipo**: feature
- **Objetivo**: Implementar o motor de comparação entre a autoavaliação do estudante e as evidências práticas registradas pelo professor.
- **Descrição**: Criar DiagnosticService que consulta vw_self_eval_discrepancy (DB-038). Para cada competência: (1) Se |perceived - verified| <= 0.8 -> ALIGNED; (2) Se perceived - verified >= 1.5 -> OVERCONFIDENCE_RISK (aluno acha que domina, mas falhou na prática/tolerância); (3) Se verified - perceived >= 1.5 -> UNDERCONFIDENCE_SUPPORT (aluno domina a prática, mas está inseguro); (4) Sem entregas avaliadas -> INSUFFICIENT_EVIDENCE. Grava em explainable_diagnostics com critérios, evidências e limitações explícitas.
- **História de Usuário**: Como Professor, quero um diagnóstico explicável que compare a autoavaliação do aluno com as notas práticas reais, destacando divergências que mereçam mentoria.
- **Critérios de Aceitação**:
- Nunca trata autoavaliação como prova definitiva de competência.
- Todo diagnóstico gerado inclui explanation_text, evidências utilizadas e limitations_note.
- Gera alerta pedagógico quando houver divergência crítica em competência de segurança ou precisão.
- **Definição de Pronto (DoD)**: Motor de diagnóstico coberto por testes unitários validando os 4 cenários.
- **Observações Técnicas**: Atende com excelência todos os requisitos da seção 4.3.

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
- **Descrição**: Implementar PATCH /api/v1/alerts/:id/resolve recebendo status ('ACKNOWLEDGED' | 'RESOLVED') e resolutionNotes obrigatórias descrevendo a ação pedagógica tomada. Registra auditoria em audit_logs.
- **História de Usuário**: Como Professor, quero registrar qual intervenção realizei para apoiar um aluno em alerta e marcar o acompanhamento como concluído.
- **Critérios de Aceitação**:
- Rota: PATCH /api/v1/alerts/:id/resolve (HTTP 200).
- Exige preenchimento de resolutionNotes (mínimo 10 caracteres).
- Grava resolved_by com o ID do professor autenticado.
- **Definição de Pronto (DoD)**: Endpoint testado e integrado às ações rápidas do card de risco (FE-032).
- **Observações Técnicas**: Mantém o histórico completo de intervenções na ficha 360° do aluno.

---

### [BE-040] Testes de Carga e Performance nas Rotas de Dashboard
- **ID**: `BE-040`
- **Título**: Testes de Carga e Performance nas Rotas de Dashboard
- **Área**: Back-end
- **Epic**: EPIC-05: Dashboard Híbrido do Professor & Visão 360°
- **Lote / Sprint**: Lote 4 (S4)
- **Sequência na Squad**: ⬅️ Anterior: `BE-039` | ➡️ Próximo: `BE-041`
- **Dependências Diretas**: `BE-031, BE-032, BE-033, BE-034, BE-035, BE-036, BE-037, BE-038, BE-039, DB-040`
- **Prioridade**: P1 | **Estimativa**: 3 SP | **Tipo**: teste
- **Objetivo**: Validar a corretude, segurança e tempo de resposta de todas as rotas analíticas, dashboards e diagnósticos do Lote 4.
- **Descrição**: Criar suíte de testes automatizados Vitest verificando: motor de risco (BE-032), cruzamento diagnóstico (BE-037), isolamento de dados no portal do aluno (BE-034) e benchmark de tempo de resposta (<200ms) com os dados do seed (DB-040).
- **História de Usuário**: Como Tech Lead, quero garantir que os dashboards e motores de diagnóstico respondam rápido e sem falhas de segurança.
- **Critérios de Aceitação**:
- Cobertura >= 80% nos serviços RiskEngineService e DiagnosticService.
- Confirmação de zero vazamento de dados entre estudantes.
- Tempo de resposta médio das rotas de dashboard abaixo de 200ms.
- **Definição de Pronto (DoD)**: Suíte de testes do Lote 4 passando 100%.
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
- **Descrição**: Implementar POST /api/v1/announcements, PATCH /api/v1/announcements/:id e DELETE /api/v1/announcements/:id. Valida se o autor é professor da turma ou coordenador. Suporta prioridade (NORMAL, IMPORTANT, URGENT) e fixação no topo (isPinned).
- **História de Usuário**: Como Professor, quero publicar avisos oficiais para minha turma sobre aulas práticas, materiais e avaliações.
- **Critérios de Aceitação**:
- Rota: POST /api/v1/announcements (HTTP 201 Created).
- Bloqueia criação de avisos por usuários com perfil STUDENT (HTTP 403).
- Validação Zod de título, conteúdo e classId.
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
- **Descrição**: Retornar avisos ordenados por is_pinned DESC e published_at DESC, com suporte a paginação e filtro por classId, subjectId e priority. Estudantes visualizam apenas avisos das turmas em que estão matriculados.
- **História de Usuário**: Como Estudante ou Professor, quero consultar os avisos da minha turma filtrando por disciplina.
- **Critérios de Aceitação**:
- Rota: GET /api/v1/announcements (HTTP 200 OK).
- Filtra automaticamente avisos expirados (expires_at < NOW()).
- Isolamento por turma: aluno de outra turma recebe HTTP 403 se tentar filtrar turma alheia.
- **Definição de Pronto (DoD)**: Consulta de mural testada e pronta para FE-043.
- **Observações Técnicas**: Usa o índice composto criado em DB-041.

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
- **Descrição**: Implementar POST /api/v1/help-requests e GET /api/v1/help-requests. O aluno informa subjectId, moduleId opcional, category, subjectTitle, description e isConfidential (default true). Na listagem GET, um estudante vê estritamente os próprios pedidos; o professor vê os pedidos das suas disciplinas.
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
- **Descrição**: Implementar POST /api/v1/help-requests/:id/messages (envio de mensagem em chat_messages com atualização de leitura) e PATCH /api/v1/help-requests/:id (transição de status: OPEN -> IN_PROGRESS -> RESOLVED -> CLOSED com resolutionSummary).
- **História de Usuário**: Como Professor, quero responder ao pedido de ajuda do aluno, agendar uma mentoria e registrar o encerramento quando a dúvida for sanada.
- **Critérios de Aceitação**:
- Valida que apenas o aluno autor do pedido, o professor responsável ou a coordenação podem ler ou enviar mensagens no chamado.
- Atualiza is_read = true e read_at quando o destinatário visualiza as mensagens.
- Registra closed_at ao encerrar a solicitação.
- **Definição de Pronto (DoD)**: Fluxo completo de mensagens e estados de solicitação validado e integrado a FE-044 e FE-045.
- **Observações Técnicas**: Cumpre o controle de estados de leitura, resposta e encerramento (seção 4.4).

---

### [BE-045] Endpoint para Registro de Observações Pedagógicas com Acesso Restrito
- **ID**: `BE-045`
- **Título**: Endpoint para Registro de Observações Pedagógicas com Acesso Restrito
- **Área**: Back-end
- **Epic**: EPIC-08: Comunicação Oficial & Solicitações Confidenciais
- **Lote / Sprint**: Lote 5 (S5)
- **Sequência na Squad**: ⬅️ Anterior: `BE-044` | ➡️ Próximo: `BE-046`
- **Dependências Diretas**: `BE-009, DB-009, DB-043`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Disponibilizar endpoints estritamente protegidos para docentes e coordenadores registrarem e consultarem observações pedagógicas sobre estudantes.
- **Descrição**: Implementar POST /api/v1/pedagogical-notes e GET /api/v1/students/:id/pedagogical-notes. Bloqueia terminantemente qualquer acesso por usuários com role STUDENT. Filtra o retorno conforme visibility_scope: PRIVATE_AUTHOR (só o próprio autor vê), TEACHERS_AND_COORD (docentes da turma e coordenação) ou COORDINATION_ONLY.
- **História de Usuário**: Como Professor ou Coordenador, quero registrar anotações pedagógicas de acompanhamento com controle estrito de quem pode visualizá-las.
- **Critérios de Aceitação**:
- Qualquer tentativa de acesso por perfil STUDENT retorna HTTP 403 Forbidden e gera alerta em audit_logs.
- Respeita rigorosamente o visibility_scope de cada nota.
- Suporta agendamento de acompanhamento (requiresFollowup e followupDate).
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
- **Objetivo**: Automatizar a concessão de XP, evolução de nível (Iniciante, Praticante, Proficiente, Especialista) e desbloqueio de badges quando o aluno conclui módulos e práticas.
- **Descrição**: Criar GamificationService acionado após avaliação prática (BE-025) e fechamento de módulo (BE-028). Verifica se os critérios objetivos de gamification_badges foram atingidos, grava em student_achievements e adiciona marco em student_milestone_history.
- **História de Usuário**: Como Estudante, quero subir de nível e desbloquear conquistas automaticamente quando minhas peças práticas forem aprovadas pelo professor.
- **Critérios de Aceitação**:
- Regra de pontuação determinística, documentada e calculada 100% no servidor.
- Idempotente: não concede a mesma badge duas vezes ao mesmo aluno.
- Registra marco na linha do tempo do estudante (DB-039).
- **Definição de Pronto (DoD)**: Serviço testado unitariamente e integrado ao fluxo de avaliação prática.
- **Observações Técnicas**: Conecta as entregas de oficina (EPIC-04) com a gamificação (EPIC-09).

---

### [BE-048] Middleware de Registro de Ações Sensíveis no Log de Auditoria
- **ID**: `BE-048`
- **Título**: Middleware de Registro de Ações Sensíveis no Log de Auditoria
- **Área**: Back-end
- **Epic**: EPIC-10: Relatórios, Governança de Dados & Qualidade
- **Lote / Sprint**: Lote 5 (S5)
- **Sequência na Squad**: ⬅️ Anterior: `BE-047` | ➡️ Próximo: `BE-049`
- **Dependências Diretas**: `BE-009, BE-019, BE-027, BE-039, BE-045, DB-009`
- **Prioridade**: P1 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Rastrear automaticamente todas as operações críticas (alteração de notas, status de matrícula, leitura/escrita de notas pedagógicas e resolução de alertas).
- **Descrição**: Implementar AuditService e hook/middleware que grava em audit_logs (DB-009): userId, action, entity, entityId, oldValues (mascarando senhas/segredos), newValues, ipAddress e timestamp. Disponibilizar GET /api/v1/admin/audit-logs restrito a ADMIN e COORDINATOR.
- **História de Usuário**: Como Coordenador ou Auditor, quero consultar o histórico de alterações sensíveis sem que dados pessoais desnecessários vazem em logs.
- **Critérios de Aceitação**:
- Grava auditoria automática nas rotas de notas, matrículas, alertas e observações restritas.
- Sanitiza campos sensíveis (password, tokens) antes de persistir.
- Endpoint GET /api/v1/admin/audit-logs paginado e filtrado por entidade e período.
- **Definição de Pronto (DoD)**: Auditoria ativa e verificada por testes de integração.
- **Observações Técnicas**: Atende aos requisitos de segurança, logs e auditoria (seções 8 e 14).

---

### [BE-049] Exportação de Relatórios de Desempenho em Formato CSV / PDF
- **ID**: `BE-049`
- **Título**: Exportação de Relatórios de Desempenho em Formato CSV / PDF
- **Área**: Back-end
- **Epic**: EPIC-10: Relatórios, Governança de Dados & Qualidade
- **Lote / Sprint**: Lote 5 (S5)
- **Sequência na Squad**: ⬅️ Anterior: `BE-048` | ➡️ Próximo: `BE-050`
- **Dependências Diretas**: `BE-031, DB-036, DB-047`
- **Prioridade**: P1 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Disponibilizar endpoint GET /api/v1/reports/performance para exportação de relatórios consolidados de turma, notas, frequência e evolução por módulo.
- **Descrição**: Permitir que professores e coordenadores exportem dados consolidados da turma (filtrando por classId, subjectId, moduleId e format='csv'|'json') para reuniões de conselho de classe SENAI. Configura headers Content-Disposition e Content-Type adequados.
- **História de Usuário**: Como Coordenador ou Professor, quero exportar o relatório consolidado da turma em CSV/PDF para apresentar no conselho de classe.
- **Critérios de Aceitação**:
- Rota: GET /api/v1/reports/performance?classId=...&format=csv.
- Não inclui observações confidenciais privadas no relatório geral exportado.
- Consulta otimizada utilizando os índices de DB-047 e a view DB-036.
- **Definição de Pronto (DoD)**: Exportação funcionando e integrada à central de relatórios no frontend (FE-048).
- **Observações Técnicas**: Codificação UTF-8 com BOM no CSV para abrir acentuação corretamente no Excel.

---

### [BE-050] Geração Automatizada de Documentação Interativa com Swagger/OpenAPI
- **ID**: `BE-050`
- **Título**: Geração Automatizada de Documentação Interativa com Swagger/OpenAPI
- **Área**: Back-end
- **Epic**: EPIC-10: Relatórios, Governança de Dados & Qualidade
- **Lote / Sprint**: Lote 5 (S5)
- **Sequência na Squad**: ⬅️ Anterior: `BE-049` | ➡️ Próximo: `Marco Final Concluído (100%)`
- **Dependências Diretas**: `BE-001, BE-010, BE-020, BE-030, BE-040, BE-048, BE-049, DB-050`
- **Prioridade**: P0 | **Estimativa**: 2 SP | **Tipo**: documentacao
- **Objetivo**: Consolidar e publicar a documentação interativa OpenAPI 3.0 (/docs) de todos os 50 cards de back-end e validar o contrato final com o Front-end (FE-050) e Banco (DB-050).
- **Descrição**: Configurar @fastify/swagger e @fastify/swagger-ui integrados aos schemas Zod de todas as rotas (Lotes 1 a 5), incluindo esquemas de autenticação Bearer JWT, exemplos de payload, códigos HTTP e exportar o arquivo openapi-spec.json para DOC-013.
- **História de Usuário**: Como Equipe de Desenvolvimento e Banca Avaliadora, queremos explorar e testar todas as rotas da API em uma interface Swagger completa e documentada.
- **Critérios de Aceitação**:
- Rota GET /docs exibe Swagger UI com todas as rotas agrupadas por tag (Auth, Academic, Diary, PracticalTasks, Dashboard, Diagnostics, Communication, Gamification, Reports).
- Exporta especificação OpenAPI válida para docs/api/openapi-spec.json (DOC-013).
- Todos os testes de back-end (Lotes 1 a 5) passando 100%.
- **Definição de Pronto (DoD)**: Camada de Back-end 100% concluída, documentada no Swagger e integrada com DB-050, FE-050 e DOC-020.
- **Observações Técnicas**: Marco de encerramento (Card 50/50) da squad de Back-end.

