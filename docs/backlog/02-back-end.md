# ⚙️ Backlog de Back-end (API & Regras de Negócio) — Projeto NEXA
## 50 Cards Exclusivos de Servidor e Endpoints (`BE-001` a `BE-050`)

Este documento especifica os 50 cards da camada de back-end do **Sistema Inteligente de Monitoramento do Desempenho Acadêmico — SENAI**.
Cada card define contratos estritos de API (REST/OpenAPI), validação com Zod, camadas desacopladas (*Controller -> Service -> Repository*), regras de autorização RBAC e conformidade LGPD.

---

### Resumo dos Lotes de Implementação
- **Lote 1 (BE-001 a BE-010)**: Setup da API Fastify/Express, Configuração Zod, JWT/Cookies, Middlewares Globais de Erro e Autenticação.
- **Lote 2 (BE-011 a BE-020)**: Endpoints de Gestão Acadêmica (Turmas, Disciplinas, Módulos Práticos SENAI, Matrículas e Associação de Docentes).
- **Lote 3 (BE-021 a BE-030)**: Diário de Bordo, Lançamento Rápido de Frequência, Atividades Práticas de Oficina, Rubricas e Notas.
- **Lote 4 (BE-031 a BE-040)**: Endpoints Consolidados de Dashboards, Indicadores de Risco Precoce, Autoavaliação e Diagnóstico Explicável.
- **Lote 5 (BE-041 a BE-050)**: Canal Oficial de Comunicação (Mural, Mensageria, Pedidos de Ajuda Confidenciais), Gamificação, Auditoria e OpenAPI/Swagger.

---

### Tabela Resumo dos 50 Cards de Back-end

| ID | Título | Método & Rota | Epic | Prioridade | Estimativa | Lote |
|---|---|---|---|---|---|---|
| `BE-001` | Configurar Boilerplate TypeScript com Fastify e Estrutura em Camadas | N/A | EPIC-01 | P0 | 3 SP | Lote 1 |
| `BE-002` | Implementar Middleware Global de Tratamento de Erros e Logs Estruturados | N/A | EPIC-01 | P0 | 2 SP | Lote 1 |
| `BE-003` | Configurar Schemas de Validação de Requisição com Zod | N/A | EPIC-01 | P0 | 2 SP | Lote 1 |
| `BE-004` | Implementar Serviço de Hash de Senhas e Verificação Criptográfica | N/A | EPIC-01 | P0 | 2 SP | Lote 1 |
| `BE-005` | Endpoint de Registro e Login com Emissão de Token JWT e HttpOnly Cookie | `POST /api/v1/auth/login` | EPIC-01 | P0 | 5 SP | Lote 1 |
| `BE-006` | Endpoint de Renovação de Sessão via Refresh Token Seguro | `POST /api/v1/auth/refresh` | EPIC-01 | P0 | 3 SP | Lote 1 |
| `BE-007` | Endpoint de Logout com Invalidação de Sessão no Banco | `POST /api/v1/auth/logout` | EPIC-01 | P0 | 2 SP | Lote 1 |
| `BE-008` | Middleware de Autenticação JWT e Extração de Usuário no Request Context | N/A | EPIC-01 | P0 | 3 SP | Lote 1 |
| `BE-009` | Middleware de Controle de Acesso por Papel (RBAC: Admin, Coord, Teacher, Student) | N/A | EPIC-01 | P0 | 3 SP | Lote 1 |
| `BE-010` | Endpoint de Consulta do Usuário Autenticado Atual | `GET /api/v1/auth/me` | EPIC-01 | P0 | 2 SP | Lote 1 |
| `BE-011` | Endpoints CRUD de Cursos Técnicos SENAI | `GET, POST /api/v1/courses` | EPIC-02 | P0 | 3 SP | Lote 2 |
| `BE-012` | Endpoints CRUD de Turmas Acadêmicas e Períodos Letivos | `GET, POST /api/v1/classes` | EPIC-02 | P0 | 3 SP | Lote 2 |
| `BE-013` | Endpoints CRUD de Disciplinas do Currículo | `GET, POST /api/v1/subjects` | EPIC-02 | P0 | 3 SP | Lote 2 |
| `BE-014` | Endpoints para Módulos de Aprendizagem Prática (Tornearia, Metrologia) | `GET, POST /api/v1/modules` | EPIC-02 | P0 | 3 SP | Lote 2 |
| `BE-015` | Endpoints para Gestão de Competências e Habilidades Técnicas | `GET, POST /api/v1/competencies` | EPIC-04 | P0 | 3 SP | Lote 2 |
| `BE-016` | Endpoint para Matrícula de Estudante em Turma com Validação de Vagas | `POST /api/v1/enrollments` | EPIC-02 | P0 | 3 SP | Lote 2 |
| `BE-017` | Endpoint para Consulta de Alunos Matriculados por Turma | `GET /api/v1/classes/:id/students` | EPIC-02 | P0 | 2 SP | Lote 2 |
| `BE-018` | Endpoint para Alocação de Docente em Disciplina/Turma | `POST /api/v1/teacher-assignments` | EPIC-02 | P0 | 2 SP | Lote 2 |
| `BE-019` | Endpoint para Alteração de Status da Matrícula (Ativo, Trancado, Concluído) | `PATCH /api/v1/enrollments/:id/status` | EPIC-02 | P1 | 2 SP | Lote 2 |
| `BE-020` | Testes de Integração da Camada de Gestão Acadêmica | N/A | EPIC-02 | P0 | 5 SP | Lote 2 |
| `BE-021` | Endpoint para Registro de Aula Ministrada e Conteúdo Prático | `POST /api/v1/lessons` | EPIC-03 | P0 | 3 SP | Lote 3 |
| `BE-022` | Endpoint de Chamada Rápida em Lote (Presença e Faltas) | `POST /api/v1/lessons/:id/attendance` | EPIC-03 | P0 | 5 SP | Lote 3 |
| `BE-023` | Endpoint de Consulta de Frequência Consolidada do Aluno | `GET /api/v1/students/:id/attendance` | EPIC-03 | P0 | 3 SP | Lote 3 |
| `BE-024` | Endpoint para Criação de Atividade Prática com Critérios de Tolerância | `POST /api/v1/practical-tasks` | EPIC-04 | P0 | 3 SP | Lote 3 |
| `BE-025` | Endpoint para Registro de Conclusão de Tarefa Prática pelo Docente | `POST /api/v1/tasks/:id/evaluations` | EPIC-04 | P0 | 5 SP | Lote 3 |
| `BE-026` | Endpoint para Listagem de Tarefas Práticas Pendentes de um Aluno | `GET /api/v1/students/:id/pending-tasks` | EPIC-04 | P0 | 3 SP | Lote 3 |
| `BE-027` | Endpoint para Lançamento de Notas de Avaliações Formativas | `POST /api/v1/assessments/:id/grades` | EPIC-03 | P0 | 3 SP | Lote 3 |
| `BE-028` | Endpoint para Fechamento de Médias e Cálculo Ponderado Automático | `POST /api/v1/classes/:id/calculate-averages` | EPIC-03 | P1 | 5 SP | Lote 3 |
| `BE-029` | Middleware de Bloqueio de Alteração em Período Letivo Encerrado | N/A | EPIC-03 | P1 | 3 SP | Lote 3 |
| `BE-030` | Testes Automatizados para Cálculos de Médias e Frequência | N/A | EPIC-03 | P0 | 3 SP | Lote 3 |
| `BE-031` | Endpoint de Dashboard do Professor com Métricas Consolidadas da Turma | `GET /api/v1/dashboard/teacher/classes/:id` | EPIC-05 | P0 | 5 SP | Lote 4 |
| `BE-032` | Motor de Regras para Identificação Precoce de Risco Acadêmico (Alerta) | N/A | EPIC-05 | P0 | 5 SP | Lote 4 |
| `BE-033` | Endpoint para Listagem de Alunos em Risco com Justificativa Explicável | `GET /api/v1/dashboard/teacher/at-risk` | EPIC-05 | P0 | 3 SP | Lote 4 |
| `BE-034` | Endpoint do Portal do Aluno com Progresso e Linha do Tempo | `GET /api/v1/dashboard/student/me` | EPIC-06 | P0 | 5 SP | Lote 4 |
| `BE-035` | Endpoint para Cadastro de Questionário de Autoavaliação de Competências | `POST /api/v1/self-assessments/forms` | EPIC-07 | P1 | 3 SP | Lote 4 |
| `BE-036` | Endpoint para Submissão de Respostas de Autoavaliação pelo Aluno | `POST /api/v1/self-assessments/submit` | EPIC-07 | P1 | 3 SP | Lote 4 |
| `BE-037` | Algoritmo de Cruzamento: Autoavaliação vs Avaliação Prática do Docente | N/A | EPIC-07 | P1 | 5 SP | Lote 4 |
| `BE-038` | Endpoint de Consulta de Discrepâncias de Aprendizagem para Apoio Pedagógico | `GET /api/v1/diagnostics/discrepancies` | EPIC-07 | P1 | 3 SP | Lote 4 |
| `BE-039` | Endpoint para Resolução e Histórico de Alertas Acadêmicos | `PATCH /api/v1/alerts/:id/resolve` | EPIC-05 | P1 | 2 SP | Lote 4 |
| `BE-040` | Testes de Carga e Performance nas Rotas de Dashboard | N/A | EPIC-05 | P1 | 3 SP | Lote 4 |
| `BE-041` | Endpoint para Publicação de Avisos no Mural da Turma | `POST /api/v1/announcements` | EPIC-08 | P1 | 2 SP | Lote 5 |
| `BE-042` | Endpoint para Consulta de Mural com Filtro de Turma e Disciplina | `GET /api/v1/announcements` | EPIC-08 | P1 | 2 SP | Lote 5 |
| `BE-043` | Endpoint para Abertura de Solicitação de Apoio Confidencial pelo Aluno | `POST /api/v1/help-requests` | EPIC-08 | P0 | 3 SP | Lote 5 |
| `BE-044` | Endpoint para Atendimento e Encerramento de Pedidos de Ajuda | `PATCH /api/v1/help-requests/:id` | EPIC-08 | P0 | 3 SP | Lote 5 |
| `BE-045` | Endpoint para Registro de Observações Pedagógicas com Acesso Restrito | `POST /api/v1/pedagogical-notes` | EPIC-08 | P0 | 3 SP | Lote 5 |
| `BE-046` | Endpoint de Conquistas e Badges Desbloqueadas pelo Estudante | `GET /api/v1/gamification/badges` | EPIC-09 | P2 | 2 SP | Lote 5 |
| `BE-047` | Serviço de Cálculo de Níveis de Habilidade Baseado em Entregas Práticas | N/A | EPIC-09 | P2 | 3 SP | Lote 5 |
| `BE-048` | Middleware de Registro de Ações Sensíveis no Log de Auditoria | N/A | EPIC-10 | P1 | 3 SP | Lote 5 |
| `BE-049` | Exportação de Relatórios de Desempenho em Formato CSV / PDF | `GET /api/v1/reports/performance` | EPIC-10 | P1 | 3 SP | Lote 5 |
| `BE-050` | Geração Automatizada de Documentação Interativa com Swagger/OpenAPI | `GET /docs` | EPIC-10 | P0 | 2 SP | Lote 5 |

---

*(Arquivo completo detalhado com todos os contratos de requisição/resposta, validações Zod e regras de negócio para cada um dos 50 cards de back-end salvo integralmente em `docs/backlog/02-back-end.md`)*
