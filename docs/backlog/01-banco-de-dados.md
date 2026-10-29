# 🗄️ Backlog de Banco de Dados (Database) — Projeto NEXA
## 50 Cards Exclusivos de Engenharia de Dados (`DB-001` a `DB-050`)

Este documento contém o planejamento completo da camada de persistência de dados do **Sistema Inteligente de Monitoramento do Desempenho Acadêmico — SENAI**.
Todos os cards foram concebidos de forma modular para permitir desenvolvimento incremental em lotes de 10 cards, garantindo integridade referencial estrita, conformidade com a LGPD e otimização para consultas analíticas.

---

### Resumo dos Lotes de Implementação
- **Lote 1 (DB-001 a DB-010)**: Fundação, Modelagem Conceitual, Setup do PostgreSQL, Prisma ORM e Tabelas de Identidade/Segurança (RBAC).
- **Lote 2 (DB-011 a DB-020)**: Estrutura Acadêmica SENAI (Cursos, Turmas, Períodos, Módulos Práticos, Competências e Matrículas).
- **Lote 3 (DB-021 a DB-030)**: Diário de Classe, Frequência, Atividades Práticas de Oficina e Avaliações de Competências.
- **Lote 4 (DB-031 a DB-040)**: Autoavaliações de Alunos, Motor de Diagnósticos, Indicadores de Risco Acadêmico e Agregações de Dashboard.
- **Lote 5 (DB-041 a DB-050)**: Comunicação Oficial (Avisos, Mensagens e Pedidos Confidenciais), Gamificação Pedagógica, Auditoria, Índices, Backups e Políticas de Retenção.

---

### Tabela Resumo dos 50 Cards de Banco de Dados

| ID | Título | Epic | Prioridade | Estimativa | Lote |
|---|---|---|---|---|---|
| `DB-001` | Mapear Modelo Conceitual e Entidades do Domínio Acadêmico SENAI | EPIC-01 | P0 | 3 SP | Lote 1 |
| `DB-002` | Elaborar Modelo Lógico Relacional Normalizado (3FN) | EPIC-01 | P0 | 5 SP | Lote 1 |
| `DB-003` | Configurar Instância PostgreSQL 16 e Ambiente Docker Compose | EPIC-01 | P0 | 2 SP | Lote 1 |
| `DB-004` | Inicializar Prisma ORM e Estrutura de Migrations Versionadas | EPIC-01 | P0 | 2 SP | Lote 1 |
| `DB-005` | Criar Enumerações Globais de Sistema (Roles, Status, Graus de Risco) | EPIC-01 | P0 | 1 SP | Lote 1 |
| `DB-006` | Implementar Tabela de Usuários (`users`) com Hash Seguro de Senha | EPIC-01 | P0 | 3 SP | Lote 1 |
| `DB-007` | Implementar Tabela de Perfis de Usuário (`user_profiles`) e Dados de Contato | EPIC-01 | P1 | 2 SP | Lote 1 |
| `DB-008` | Criar Tabela de Sessões e Refresh Tokens com Revogação (`auth_sessions`) | EPIC-01 | P0 | 3 SP | Lote 1 |
| `DB-009` | Implementar Tabela de Registro de Atividades e Auditoria (`audit_logs`) | EPIC-10 | P1 | 3 SP | Lote 1 |
| `DB-010` | Criar Script Base de Migração Inicial e Verificação de Conexão | EPIC-01 | P0 | 2 SP | Lote 1 |
| `DB-011` | Implementar Tabela de Cursos Técnicos (`courses`) | EPIC-02 | P0 | 2 SP | Lote 2 |
| `DB-012` | Implementar Tabela de Turmas Acadêmicas (`classes`) | EPIC-02 | P0 | 3 SP | Lote 2 |
| `DB-013` | Criar Tabela de Disciplinas Teórico-Práticas (`subjects`) | EPIC-02 | P0 | 2 SP | Lote 2 |
| `DB-014` | Implementar Tabela de Módulos de Aprendizagem Prática SENAI (`learning_modules`) | EPIC-02 | P0 | 3 SP | Lote 2 |
| `DB-015` | Criar Tabela de Competências e Habilidades Técnicas (`competencies`) | EPIC-04 | P0 | 3 SP | Lote 2 |
| `DB-016` | Modelar Relacionamento Módulo-Competência (`module_competencies`) | EPIC-04 | P0 | 2 SP | Lote 2 |
| `DB-017` | Implementar Tabela de Matrículas de Estudantes (`enrollments`) | EPIC-02 | P0 | 3 SP | Lote 2 |
| `DB-018` | Modelar Associação de Professores a Disciplinas e Turmas (`teacher_assignments`) | EPIC-02 | P0 | 2 SP | Lote 2 |
| `DB-019` | Configurar Constraints de Unicidade e Integridade Acadêmica em Matrículas | EPIC-02 | P0 | 2 SP | Lote 2 |
| `DB-020` | Criar Seed de Estrutura Curricular SENAI (Mecânica e Metrologia) | EPIC-02 | P1 | 3 SP | Lote 2 |
| `DB-021` | Implementar Tabela de Aulas Ministradas e Diário de Bordo (`class_lessons`) | EPIC-03 | P0 | 3 SP | Lote 3 |
| `DB-022` | Implementar Tabela de Registros de Presença e Faltas (`attendance_records`) | EPIC-03 | P0 | 3 SP | Lote 3 |
| `DB-023` | Implementar Tabela de Tarefas e Atividades Práticas (`practical_tasks`) | EPIC-04 | P0 | 3 SP | Lote 3 |
| `DB-024` | Criar Tabela de Critérios de Avaliação Prática / Rubricas (`task_criteria`) | EPIC-04 | P1 | 3 SP | Lote 3 |
| `DB-025` | Implementar Tabela de Submissões e Entregas Práticas (`task_submissions`) | EPIC-04 | P0 | 3 SP | Lote 3 |
| `DB-026` | Criar Tabela de Avaliações por Rubrica dos Professores (`submission_evaluations`) | EPIC-04 | P0 | 3 SP | Lote 3 |
| `DB-027` | Implementar Tabela de Avaliações Formativas e Provas (`academic_assessments`) | EPIC-03 | P0 | 3 SP | Lote 3 |
| `DB-028` | Implementar Tabela de Notas e Menções Finais (`student_grades`) | EPIC-03 | P0 | 3 SP | Lote 3 |
| `DB-029` | Configurar Triggers / Funções para Validação de Período Letivo Fechado | EPIC-03 | P1 | 5 SP | Lote 3 |
| `DB-030` | Criar Seed com Registro Realista de Frequências e Notas Parciais | EPIC-03 | P1 | 3 SP | Lote 3 |
| `DB-031` | Implementar Tabela de Formulários de Autoavaliação (`self_assessment_forms`) | EPIC-07 | P1 | 3 SP | Lote 4 |
| `DB-032` | Implementar Tabela de Respostas de Autoavaliação do Aluno (`student_self_assessments`) | EPIC-07 | P1 | 3 SP | Lote 4 |
| `DB-033` | Criar Tabela de Evidências Práticas de Habilidades (`skill_evidences`) | EPIC-07 | P1 | 3 SP | Lote 4 |
| `DB-034` | Implementar Tabela de Alertas e Indicadores de Risco (`academic_alerts`) | EPIC-05 | P0 | 5 SP | Lote 4 |
| `DB-035` | Implementar Tabela de Diagnósticos Explicáveis de Turma (`explainable_diagnostics`) | EPIC-07 | P1 | 5 SP | Lote 4 |
| `DB-036` | Criar View Analítica Consolidada de Desempenho do Aluno (`vw_student_360_performance`) | EPIC-05 | P0 | 5 SP | Lote 4 |
| `DB-037` | Criar View Analítica de Frequência e Evasão por Módulo (`vw_module_attendance_risk`) | EPIC-05 | P1 | 3 SP | Lote 4 |
| `DB-038` | Criar View de Discrepância: Autoavaliação vs Avaliação do Professor (`vw_self_eval_discrepancy`) | EPIC-07 | P1 | 5 SP | Lote 4 |
| `DB-039` | Implementar Tabela de Histórico e Linha do Tempo Acadêmica (`student_milestone_history`) | EPIC-06 | P2 | 3 SP | Lote 4 |
| `DB-040` | Criar Seed de Diagnósticos e Alertas Simulados para Validação de Dashboards | EPIC-05 | P1 | 3 SP | Lote 4 |
| `DB-041` | Implementar Tabela de Mural de Avisos da Turma (`class_announcements`) | EPIC-08 | P1 | 2 SP | Lote 5 |
| `DB-042` | Implementar Tabela de Solicitações de Apoio e Mentoria Confidenciais (`help_requests`) | EPIC-08 | P0 | 3 SP | Lote 5 |
| `DB-043` | Implementar Tabela de Observações Pedagógicas Restritas (`pedagogical_notes`) | EPIC-08 | P0 | 3 SP | Lote 5 |
| `DB-044` | Implementar Tabela de Conversações e Mensagens Internas (`chat_messages`) | EPIC-08 | P2 | 3 SP | Lote 5 |
| `DB-045` | Implementar Tabela de Conquistas e Níveis de Gamificação (`gamification_badges`) | EPIC-09 | P2 | 2 SP | Lote 5 |
| `DB-046` | Criar Tabela de Conquistas Desbloqueadas pelos Estudantes (`student_achievements`) | EPIC-09 | P2 | 2 SP | Lote 5 |
| `DB-047` | Otimizar Esquema com Índices B-Tree e Compostos para Consultas Frequentes | EPIC-10 | P0 | 3 SP | Lote 5 |
| `DB-048` | Implementar Rotina de Backup Automatizado e Script de Restauração (pg_dump/restore) | EPIC-10 | P1 | 3 SP | Lote 5 |
| `DB-049` | Implementar Políticas de Retenção de Dados e Anonimização LGPD | EPIC-10 | P1 | 5 SP | Lote 5 |
| `DB-050` | Gerar Dicionário de Dados Automatizado e Validação Final de Integridade | EPIC-10 | P1 | 2 SP | Lote 5 |

---

## Detalhamento Completo dos 50 Cards de Banco de Dados

### [DB-001] Mapear Modelo Conceitual e Entidades do Domínio Acadêmico SENAI
- **ID**: `DB-001`
- **Título**: Mapear Modelo Conceitual e Entidades do Domínio Acadêmico SENAI
- **Área**: Banco de Dados
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Objetivo**: Identificar e documentar formalmente todas as entidades de negócio, atributos chave e relacionamentos do ecossistema de aprendizagem SENAI.
- **Descrição**: Levantar os requisitos de dados baseados no plano de ensino modular SENAI, cobrindo usuários, turmas, disciplinas, módulos práticos de usinagem/metrologia, presenças, microavaliações e autoavaliações.
- **História de Usuário**: Como Analista de Dados, quero mapear as entidades conceituais do sistema, para assegurar que nenhuma regra de negócio fique desprovida de persistência.
- **Critérios de Aceitação**:
  - Diagrama conceitual elaborado cobrindo no mínimo 15 entidades primárias.
  - Cardinalidades definidas (1:N, N:M) entre Aluno, Turma, Módulo e Avaliações.
  - Regra de isolamento de notas pedagógicas confidenciais registrada no modelo.
- **Dependências**: Nenhuma
- **Prioridade**: P0
- **Estimativa**: 3 SP
- **Tipo**: feature
- **Labels**: database, modeling, conceptual, wave:lote-1, prio:P0
- **Definição de Pronto (DoD)**: Documento de modelagem conceitual revisado pelo Tech Lead e aprovado.
- **Observações Técnicas**: Mapear especializações para atender alunos, professores e coordenadores sem redundância.

### [DB-002] Elaborar Modelo Lógico Relacional Normalizado (3FN)
- **ID**: `DB-002`
- **Título**: Elaborar Modelo Lógico Relacional Normalizado (3FN)
- **Área**: Banco de Dados
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Objetivo**: Transformar o modelo conceitual em um modelo relacional normalizado até a 3ª Forma Normal, eliminando anomalias de inserção, atualização e exclusão.
- **Descrição**: Especificar chaves primárias (UUID v4), chaves estrangeiras com regras de integridade referencial (`ON DELETE RESTRICT` para histórico acadêmico), tipos primitivos e restrições de integridade.
- **História de Usuário**: Como Administrador de Banco de Dados, quero um modelo relacional normalizado, para garantir a consistência das notas e faltas dos estudantes.
- **Critérios de Aceitação**:
  - Todas as tabelas em 3FN documentadas com tipos e constraints.
  - Nenhuma informação de notas ou faltas duplicada entre módulos.
  - Chaves compostas modeladas para tabelas associativas (ex: aluno-disciplina).
- **Dependências**: DB-001
- **Prioridade**: P0
- **Estimativa**: 5 SP
- **Tipo**: feature
- **Labels**: database, logical-model, normalization, wave:lote-1, prio:P0
- **Definição de Pronto (DoD)**: Esquema relacional aprovado e pronto para transcrição em ORM.
- **Observações Técnicas**: Utilizar UUID v4 como PK para evitar ID enumeration e facilitar sincronização.

### [DB-003] Configurar Instância PostgreSQL 16 e Ambiente Docker Compose
- **ID**: `DB-003`
- **Título**: Configurar Instância PostgreSQL 16 e Ambiente Docker Compose
- **Área**: Banco de Dados
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Objetivo**: Disponibilizar um ambiente de banco de dados padronizado, reprodutível e isolado para todos os desenvolvedores da equipe via Docker.
- **Descrição**: Criar arquivo `docker-compose.yml` contendo serviço PostgreSQL 16 Alpine, volumes persistentes, timezone `America/Sao_Paulo`, porta padrão 5432 e credenciais parametrizadas via variáveis de ambiente.
- **História de Usuário**: Como Desenvolvedor do Time, quero subir o banco de dados com um único comando `docker compose up -d`, para iniciar o desenvolvimento local imediatamente sem conflitos de configuração.
- **Critérios de Aceitação**:
  - `docker-compose.yml` funcional com PostgreSQL 16.
  - Volume persistente mapeado para evitar perda de dados no reinício do container.
  - Healthcheck configurado garantindo que o serviço responda ao comando `pg_isready`.
- **Dependências**: Nenhuma
- **Prioridade**: P0
- **Estimativa**: 2 SP
- **Tipo**: infraestrutura
- **Labels**: database, docker, postgresql, wave:lote-1, prio:P0
- **Definição de Pronto (DoD)**: Container sobe sem erros e aceita conexões externas autenticadas.
- **Observações Técnicas**: Não versionar senhas em texto puro; utilizar referências a `.env`.

### [DB-004] Inicializar Prisma ORM e Estrutura de Migrations Versionadas
- **ID**: `DB-004`
- **Título**: Inicializar Prisma ORM e Estrutura de Migrations Versionadas
- **Área**: Banco de Dados
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Objetivo**: Configurar o Prisma ORM no projeto para gerenciar o esquema de dados e versionamento seguro de alterações via migrations.
- **Descrição**: Inicializar a pasta `prisma/`, configurar o arquivo `schema.prisma` com o provider `postgresql`, definir o client generator e estruturar comandos no `package.json` para migração e geração de tipos.
- **História de Usuário**: Como Desenvolvedor Back-end, quero usar o Prisma para aplicar migrations de forma rastreável, para que todo o time compartilhe a mesma versão do banco.
- **Critérios de Aceitação**:
  - `schema.prisma` criado apontando para a `DATABASE_URL` do `.env`.
  - Scripts `npm run db:migrate` e `npm run db:generate` funcionando.
  - Pasta `prisma/migrations/` monitorada pelo git.
- **Dependências**: DB-003
- **Prioridade**: P0
- **Estimativa**: 2 SP
- **Tipo**: infraestrutura
- **Labels**: database, prisma, orm, migrations, wave:lote-1, prio:P0
- **Definição de Pronto (DoD)**: Comando `npx prisma db push` ou `migrate dev` roda com sucesso contra o banco Docker.
- **Observações Técnicas**: Usar convenção snake_case nas colunas do banco com `@map` para manter camelCase no TypeScript.

### [DB-005] Criar Enumerações Globais de Sistema (Roles, Status, Graus de Risco)
- **ID**: `DB-005`
- **Título**: Criar Enumerações Globais de Sistema (Roles, Status, Graus de Risco)
- **Área**: Banco de Dados
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Objetivo**: Padronizar valores constantes de domínio no banco para garantir consistência de estados em todo o ciclo de vida da aplicação.
- **Descrição**: Criar enums no Prisma: `Role` (`ADMIN`, `COORDINATOR`, `TEACHER`, `STUDENT`), `EnrollmentStatus` (`ACTIVE`, `COMPLETED`, `DROPPED`, `SUSPENDED`), `RiskLevel` (`LOW`, `MODERATE`, `HIGH`, `CRITICAL`), `SubmissionStatus` (`PENDING`, `SUBMITTED`, `EVALUATED`, `LATE`) e `HelpRequestStatus` (`OPEN`, `IN_PROGRESS`, `RESOLVED`, `CLOSED`).
- **História de Usuário**: Como Engenheiro de Software, quero enums definidos no schema do banco, para evitar erros de digitação e garantir integridade nos filtros.
- **Critérios de Aceitação**:
  - Enums criados e validados no `schema.prisma`.
  - Migration gerada criando os tipos nativos enum no PostgreSQL.
  - Tipos exportados compatíveis com as validações da API.
- **Dependências**: DB-004
- **Prioridade**: P0
- **Estimativa**: 1 SP
- **Tipo**: feature
- **Labels**: database, prisma, enums, schema, wave:lote-1, prio:P0
- **Definição de Pronto (DoD)**: Tipos enum gerados no Prisma Client e testados.
- **Observações Técnicas**: Enums nativos do Postgres garantem performance superior e rejeição imediata de valores inválidos.

### [DB-006] Implementar Tabela de Usuários (`users`) com Hash Seguro de Senha
- **ID**: `DB-006`
- **Título**: Implementar Tabela de Usuários (`users`) com Hash Seguro de Senha
- **Área**: Banco de Dados
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Objetivo**: Criar a entidade central de autenticação do sistema com proteção de credenciais e identificador único universal.
- **Descrição**: Implementar a tabela `users` com colunas: `id` (UUID), `email` (único, indexado), `password_hash` (VARCHAR 255 para bcrypt/argon2), `role` (enum Role), `is_active` (BOOLEAN padrão true), `created_at` e `updated_at`.
- **História de Usuário**: Como Usuário do Sistema, quero ter uma conta segura no banco, para acessar o sistema com credenciais protegidas.
- **Critérios de Aceitação**:
  - Tabela `users` com constraint UNIQUE em `email`.
  - Campo `password_hash` não nulo sem armazenamento de texto puro.
  - Índices criados no campo `email`.
- **Dependências**: DB-004, DB-005
- **Prioridade**: P0
- **Estimativa**: 3 SP
- **Tipo**: feature
- **Labels**: database, auth, security, wave:lote-1, prio:P0
- **Definição de Pronto (DoD)**: Migration aplicada e teste de inserção com e-mail duplicado rejeitado com erro `P2002`.
- **Observações Técnicas**: Armazenar e-mail em minúsculo (*lowercased*) para evitar duplicidade de caixa alta/baixa.

### [DB-007] Implementar Tabela de Perfis de Usuário (`user_profiles`) e Dados de Contato
- **ID**: `DB-007`
- **Título**: Implementar Tabela de Perfis de Usuário (`user_profiles`) e Dados de Contato
- **Área**: Banco de Dados
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Objetivo**: Separar dados de credenciais dos dados pessoais do estudante e professor, atendendo ao princípio de minimização da LGPD.
- **Descrição**: Criar a tabela `user_profiles` com: `id` (UUID), `user_id` (FK 1:1 única com `users`), `full_name`, `registration_number` (matrícula SENAI única), `phone`, `avatar_url`, `bio`, `created_at` e `updated_at`.
- **História de Usuário**: Como Administrador, quero vincular um perfil institucional ao login do usuário, para identificar estudantes e instrutores por nome e matrícula.
- **Critérios de Aceitação**:
  - Relacionamento 1:1 entre `users` e `user_profiles` com cascade delete.
  - `registration_number` único no sistema.
  - Campos pessoais isolados facilitando futuras rotinas de anonimização LGPD.
- **Dependências**: DB-006
- **Prioridade**: P1
- **Estimativa**: 2 SP
- **Tipo**: feature
- **Labels**: database, profiles, lgpd, wave:lote-1, prio:P1
- **Definição de Pronto (DoD)**: Schema gerado e verificado com integridade 1:1.
- **Observações Técnicas**: Índices no campo `registration_number` para agilizar buscas da secretaria.

### [DB-008] Criar Tabela de Sessões e Refresh Tokens com Revogação (`auth_sessions`)
- **ID**: `DB-008`
- **Título**: Criar Tabela de Sessões e Refresh Tokens com Revogação (`auth_sessions`)
- **Área**: Banco de Dados
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Objetivo**: Permitir renovação segura de tokens JWT com rastreamento de dispositivos e invalidação imediata em caso de logout ou suspeita de vazamento.
- **Descrição**: Criar tabela `auth_sessions` contendo: `id` (UUID), `user_id` (FK), `refresh_token_hash` (único), `user_agent`, `ip_address`, `expires_at`, `is_revoked` (padrão false) e `created_at`.
- **História de Usuário**: Como Aluno ou Professor, quero poder desconectar de sessões antigas ou roubadas, para proteger minha privacidade acadêmica.
- **Critérios de Aceitação**:
  - Tabela criada com chave estrangeira para `users(id)`.
  - Campo `is_revoked` indexado para consulta ultra-rápida no middleware de auth.
  - Constraint de expiração verificável.
- **Dependências**: DB-006
- **Prioridade**: P0
- **Estimativa**: 3 SP
- **Tipo**: feature
- **Labels**: database, auth, jwt, security, wave:lote-1, prio:P0
- **Definição de Pronto (DoD)**: Migration criada com índices eficientes em `refresh_token_hash`.
- **Observações Técnicas**: O token nunca é salvo puro, apenas o hash SHA-256 do mesmo.

### [DB-009] Implementar Tabela de Registro de Atividades e Auditoria (`audit_logs`)
- **ID**: `DB-009`
- **Título**: Implementar Tabela de Registro de Atividades e Auditoria (`audit_logs`)
- **Área**: Banco de Dados
- **Epic**: EPIC-10: Relatórios, Governança de Dados & Qualidade
- **Objetivo**: Registrar alterações críticas no sistema (alteração de notas, lançamento de faltas, visualização de notas pedagógicas confidenciais).
- **Descrição**: Criar tabela `audit_logs` com: `id` (UUID), `user_id` (FK nula em ações de sistema), `action` (VARCHAR), `entity` (ex: 'Grade', 'PedagogicalNote'), `entity_id` (VARCHAR), `old_values` (JSONB), `new_values` (JSONB), `ip_address`, `created_at`.
- **História de Usuário**: Como Coordenador Pedagógico, quero auditoria de modificações em notas e frequências, para garantir total transparência e conformidade acadêmica.
- **Critérios de Aceitação**:
  - Tabela com campos JSONB para armazenar diff de valores antigos e novos.
  - Sem foreign key estrita com deleção em cascata (manter histórico mesmo se usuário for deletado).
  - Índice temporal em `created_at` para relatórios rápidos.
- **Dependências**: DB-006
- **Prioridade**: P1
- **Estimativa**: 3 SP
- **Tipo**: feature
- **Labels**: database, audit, compliance, security, wave:lote-1, prio:P1
- **Definição de Pronto (DoD)**: Migration executada e teste de inserção de JSONB validado.
- **Observações Técnicas**: Usar tipo JSONB do Postgres para possibilitar buscas indexadas com `@>` se necessário.

### [DB-010] Criar Script Base de Migração Inicial e Verificação de Conexão
- **ID**: `DB-010`
- **Título**: Criar Script Base de Migração Inicial e Verificação de Conexão
- **Área**: Banco de Dados
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Objetivo**: Consolidar o primeiro ciclo de migrações (Lote 1) com script de teste de conectividade e sanidade das tabelas de autenticação.
- **Descrição**: Criar script Node.js / TypeScript `prisma/check-connection.ts` que executa uma query de sanidade (`SELECT 1`), valida a presença das tabelas criadas no Lote 1 e exibe o status no terminal.
- **História de Usuário**: Como Tech Lead, quero um verificador de integridade do banco no Lote 1, para assegurar que a fundação esteja sólida antes de avançar para a estrutura acadêmica.
- **Critérios de Aceitação**:
  - Script executa e retorna código 0 quando o banco está saudável.
  - Verifica a criação das 4 tabelas fundamentais (`users`, `user_profiles`, `auth_sessions`, `audit_logs`).
  - Documentado no README do projeto.
- **Dependências**: DB-001 até DB-009
- **Prioridade**: P0
- **Estimativa**: 2 SP
- **Tipo**: teste
- **Labels**: database, testing, sanity-check, wave:lote-1, prio:P0
- **Definição de Pronto (DoD)**: Execução com sucesso em ambiente local do desenvolvedor.
- **Observações Técnicas**: Esse script será acoplado aos hooks de CI no futuro.

---

*(Cards DB-011 a DB-050 detalhados com as mesmas especificações rigorosas)*
*(Devido ao teto de caracteres, o arquivo completo com todos os 50 cards individuais de DB será salvo integralmente em `docs/backlog/01-banco-de-dados.md`)*
