# 🗄️ Backlog de Banco de Dados (Database) — Projeto NEXA
## 50 Cards Exclusivos e Encadeados de Engenharia de Dados (`DB-001` a `DB-050`)

Este documento contém o planejamento completo e 100% interligado da camada de persistência de dados do **Sistema Inteligente de Monitoramento do Desempenho Acadêmico — SENAI (NEXA)**. Ao concluir o card `DB-050`, toda a infraestrutura de dados, views analíticas, segurança LGPD e governança está finalizada.

---

### Resumo dos Lotes / Sprints de Implementação
- **Lote 1 / Sprint 1 (DB-001 a DB-010)**: Fundação, Modelagem Conceitual/Lógica, PostgreSQL 16, Prisma ORM e Tabelas de Identidade/Segurança (RBAC).
- **Lote 2 / Sprint 2 (DB-011 a DB-020)**: Estrutura Acadêmica SENAI (Cursos, Turmas, Disciplinas, Módulos Práticos, Competências e Matrículas).
- **Lote 3 / Sprint 3 (DB-021 a DB-030)**: Diário de Classe, Frequência, Atividades Práticas de Oficina, Rubricas e Notas Formativas.
- **Lote 4 / Sprint 4 (DB-031 a DB-040)**: Autoavaliações, Evidências de Habilidades, Motor de Diagnósticos Explicáveis e Views Analíticas 360°.
- **Lote 5 / Sprint 5 (DB-041 a DB-050)**: Comunicação Oficial, Canal de Ajuda Confidencial, Notas Pedagógicas Criptografadas, Gamificação, Índices, Backup e Fechamento LGPD.

---

### Tabela Geral Encadeada (50 Cards)

| ID | Título | Epic | Prioridade | Estimativa | Lote / Sprint | Dependências |
|---|---|---|---|---|---|---|
| `DB-001` | Mapear Modelo Conceitual e Entidades do Domínio Acadêmico SENAI | EPIC-01 | P0 | 3 SP | Lote 1 (S1) | `Nenhuma` |
| `DB-002` | Elaborar Modelo Lógico Relacional Normalizado (3FN) | EPIC-01 | P0 | 5 SP | Lote 1 (S1) | `DB-001` |
| `DB-003` | Configurar Instância PostgreSQL 16 e Ambiente Docker Compose | EPIC-01 | P0 | 2 SP | Lote 1 (S1) | `Nenhuma` |
| `DB-004` | Inicializar Prisma ORM e Estrutura de Migrations Versionadas | EPIC-01 | P0 | 2 SP | Lote 1 (S1) | `DB-003` |
| `DB-005` | Criar Enumerações Globais de Sistema (Roles, Status, Graus de Risco) | EPIC-01 | P0 | 1 SP | Lote 1 (S1) | `DB-004` |
| `DB-006` | Implementar Tabela de Usuários (users) com Hash Seguro de Senha | EPIC-01 | P0 | 3 SP | Lote 1 (S1) | `DB-004, DB-005` |
| `DB-007` | Implementar Tabela de Perfis de Usuário (user_profiles) e Dados de Contato | EPIC-01 | P1 | 2 SP | Lote 1 (S1) | `DB-006` |
| `DB-008` | Criar Tabela de Sessões e Refresh Tokens com Revogação (auth_sessions) | EPIC-01 | P0 | 3 SP | Lote 1 (S1) | `DB-006` |
| `DB-009` | Implementar Tabela de Registro de Atividades e Auditoria (audit_logs) | EPIC-10 | P1 | 3 SP | Lote 1 (S1) | `DB-006` |
| `DB-010` | Criar Script Base de Migração Inicial e Verificação de Conexão | EPIC-01 | P0 | 2 SP | Lote 1 (S1) | `DB-001 até DB-009` |
| `DB-011` | Implementar Tabela de Cursos Técnicos (courses) | EPIC-02 | P0 | 2 SP | Lote 2 (S2) | `DB-004` |
| `DB-012` | Implementar Tabela de Turmas Acadêmicas (classes) | EPIC-02 | P0 | 3 SP | Lote 2 (S2) | `DB-011` |
| `DB-013` | Criar Tabela de Disciplinas Teórico-Práticas (subjects) | EPIC-02 | P0 | 2 SP | Lote 2 (S2) | `DB-011` |
| `DB-014` | Implementar Tabela de Módulos de Aprendizagem Prática SENAI (learning_modules) | EPIC-02 | P0 | 3 SP | Lote 2 (S2) | `DB-013` |
| `DB-015` | Criar Tabela de Competências e Habilidades Técnicas (competencies) | EPIC-04 | P0 | 3 SP | Lote 2 (S2) | `DB-005` |
| `DB-016` | Modelar Relacionamento Módulo-Competência (module_competencies) | EPIC-04 | P0 | 2 SP | Lote 2 (S2) | `DB-014, DB-015` |
| `DB-017` | Implementar Tabela de Matrículas de Estudantes (enrollments) | EPIC-02 | P0 | 3 SP | Lote 2 (S2) | `DB-006, DB-012` |
| `DB-018` | Modelar Associação de Professores a Disciplinas e Turmas (teacher_assignments) | EPIC-02 | P0 | 2 SP | Lote 2 (S2) | `DB-006, DB-012, DB-013` |
| `DB-019` | Configurar Constraints de Unicidade e Integridade Acadêmica em Matrículas | EPIC-02 | P0 | 2 SP | Lote 2 (S2) | `DB-017` |
| `DB-020` | Criar Seed de Estrutura Curricular SENAI (Mecânica e Metrologia) | EPIC-02 | P1 | 3 SP | Lote 2 (S2) | `DB-011, DB-012, DB-013, DB-014, DB-015, DB-016, DB-017, DB-018` |
| `DB-021` | Implementar Tabela de Aulas Ministradas e Diário de Bordo (class_lessons) | EPIC-03 | P0 | 3 SP | Lote 3 (S3) | `DB-012, DB-013, DB-014, DB-018` |
| `DB-022` | Implementar Tabela de Registros de Presença e Faltas (attendance_records) | EPIC-03 | P0 | 3 SP | Lote 3 (S3) | `DB-017, DB-021` |
| `DB-023` | Implementar Tabela de Tarefas e Atividades Práticas (practical_tasks) | EPIC-04 | P0 | 3 SP | Lote 3 (S3) | `DB-012, DB-014, DB-016` |
| `DB-024` | Criar Tabela de Critérios de Avaliação Prática / Rubricas (task_criteria) | EPIC-04 | P1 | 3 SP | Lote 3 (S3) | `DB-015, DB-023` |
| `DB-025` | Implementar Tabela de Submissões e Entregas Práticas (task_submissions) | EPIC-04 | P0 | 3 SP | Lote 3 (S3) | `DB-017, DB-023` |
| `DB-026` | Criar Tabela de Avaliações por Rubrica dos Professores (submission_evaluations) | EPIC-04 | P0 | 3 SP | Lote 3 (S3) | `DB-024, DB-025` |
| `DB-027` | Implementar Tabela de Avaliações Formativas e Provas (academic_assessments) | EPIC-03 | P0 | 3 SP | Lote 3 (S3) | `DB-012, DB-013, DB-014` |
| `DB-028` | Implementar Tabela de Notas e Menções Finais (student_grades) | EPIC-03 | P0 | 3 SP | Lote 3 (S3) | `DB-017, DB-027` |
| `DB-029` | Configurar Triggers / Funções para Validação de Período Letivo Fechado | EPIC-03 | P1 | 5 SP | Lote 3 (S3) | `DB-012, DB-022, DB-025, DB-028` |
| `DB-030` | Criar Seed com Registro Realista de Frequências e Notas Parciais | EPIC-03 | P1 | 3 SP | Lote 3 (S3) | `DB-020, DB-021, DB-022, DB-025, DB-026, DB-028` |
| `DB-031` | Implementar Tabela de Formulários de Autoavaliação (self_assessment_forms) | EPIC-07 | P1 | 3 SP | Lote 4 (S4) | `DB-012, DB-014, DB-016` |
| `DB-032` | Implementar Tabela de Respostas de Autoavaliação do Aluno (student_self_assessments) | EPIC-07 | P1 | 3 SP | Lote 4 (S4) | `DB-015, DB-017, DB-031` |
| `DB-033` | Criar Tabela de Evidências Práticas de Habilidades (skill_evidences) | EPIC-07 | P1 | 3 SP | Lote 4 (S4) | `DB-015, DB-026, DB-028` |
| `DB-034` | Implementar Tabela de Alertas e Indicadores de Risco (academic_alerts) | EPIC-05 | P0 | 5 SP | Lote 4 (S4) | `DB-005, DB-017, DB-022, DB-025, DB-028` |
| `DB-035` | Implementar Tabela de Diagnósticos Explicáveis de Turma (explainable_diagnostics) | EPIC-07 | P1 | 5 SP | Lote 4 (S4) | `DB-032, DB-033, DB-034` |
| `DB-036` | Criar View Analítica Consolidada de Desempenho do Aluno (vw_student_360_performance) | EPIC-05 | P0 | 5 SP | Lote 4 (S4) | `DB-017, DB-022, DB-025, DB-028, DB-034` |
| `DB-037` | Criar View Analítica de Frequência e Evasão por Módulo (vw_module_attendance_risk) | EPIC-05 | P1 | 3 SP | Lote 4 (S4) | `DB-014, DB-021, DB-022` |
| `DB-038` | Criar View de Discrepância: Autoavaliação vs Avaliação do Professor (vw_self_eval_discrepancy) | EPIC-07 | P1 | 5 SP | Lote 4 (S4) | `DB-032, DB-033, DB-035` |
| `DB-039` | Implementar Tabela de Histórico e Linha do Tempo Acadêmica (student_milestone_history) | EPIC-06 | P2 | 3 SP | Lote 4 (S4) | `DB-014, DB-017, DB-025` |
| `DB-040` | Criar Seed de Diagnósticos e Alertas Simulados para Validação de Dashboards | EPIC-05 | P1 | 3 SP | Lote 4 (S4) | `DB-030, DB-031, DB-032, DB-033, DB-034, DB-035, DB-039` |
| `DB-041` | Implementar Tabela de Mural de Avisos da Turma (class_announcements) | EPIC-08 | P1 | 2 SP | Lote 5 (S5) | `DB-006, DB-012, DB-013` |
| `DB-042` | Implementar Tabela de Solicitações de Apoio e Mentoria Confidenciais (help_requests) | EPIC-08 | P0 | 3 SP | Lote 5 (S5) | `DB-005, DB-013, DB-014, DB-017` |
| `DB-043` | Implementar Tabela de Observações Pedagógicas Restritas (pedagogical_notes) | EPIC-08 | P0 | 3 SP | Lote 5 (S5) | `DB-006, DB-009, DB-017` |
| `DB-044` | Implementar Tabela de Conversações e Mensagens Internas (chat_messages) | EPIC-08 | P2 | 3 SP | Lote 5 (S5) | `DB-006, DB-042` |
| `DB-045` | Implementar Tabela de Conquistas e Níveis de Gamificação (gamification_badges) | EPIC-09 | P2 | 2 SP | Lote 5 (S5) | `DB-015` |
| `DB-046` | Criar Tabela de Conquistas Desbloqueadas pelos Estudantes (student_achievements) | EPIC-09 | P2 | 2 SP | Lote 5 (S5) | `DB-017, DB-045` |
| `DB-047` | Otimizar Esquema com Índices B-Tree e Compostos para Consultas Frequentes | EPIC-10 | P0 | 3 SP | Lote 5 (S5) | `DB-022, DB-025, DB-028, DB-034, DB-042` |
| `DB-048` | Implementar Rotina de Backup Automatizado e Script de Restauração (pg_dump/restore) | EPIC-10 | P1 | 3 SP | Lote 5 (S5) | `DB-003, DB-029, DB-036` |
| `DB-049` | Implementar Políticas de Retenção de Dados e Anonimização LGPD | EPIC-10 | P1 | 5 SP | Lote 5 (S5) | `DB-006, DB-007, DB-009, DB-042, DB-043` |
| `DB-050` | Gerar Dicionário de Dados Automatizado e Validação Final de Integridade | EPIC-10 | P0 | 2 SP | Lote 5 (S5) | `DB-001, DB-010, DB-020, DB-030, DB-040, DB-047, DB-048, DB-049` |

---

## Detalhamento Completo e Encadeado dos 50 Cards

### [DB-001] Mapear Modelo Conceitual e Entidades do Domínio Acadêmico SENAI
- **ID**: `DB-001`
- **Título**: Mapear Modelo Conceitual e Entidades do Domínio Acadêmico SENAI
- **Área**: Banco de Dados
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `Início da Trilha` | ➡️ Próximo: `DB-002`
- **Dependências Diretas**: `Nenhuma`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Identificar e documentar formalmente todas as entidades de negócio, atributos chave e relacionamentos do ecossistema de aprendizagem SENAI.
- **Descrição**: Levantar os requisitos de dados baseados no plano de ensino modular SENAI, cobrindo usuários, turmas, disciplinas, módulos práticos de usinagem/metrologia, presenças, microavaliações e autoavaliações.
- **História de Usuário**: Como Analista de Dados, quero mapear as entidades conceituais do sistema, para assegurar que nenhuma regra de negócio fique desprovida de persistência.
- **Critérios de Aceitação**:
- Diagrama conceitual elaborado cobrindo no mínimo 15 entidades primárias.
- Cardinalidades definidas (1:N, N:M) entre Aluno, Turma, Módulo e Avaliações.
- Regra de isolamento de notas pedagógicas confidenciais registrada no modelo.
- **Definição de Pronto (DoD)**: Documento de modelagem conceitual revisado pelo Tech Lead e aprovado.
- **Observações Técnicas**: Mapear especializações para atender alunos, professores e coordenadores sem redundância.

---

### [DB-002] Elaborar Modelo Lógico Relacional Normalizado (3FN)
- **ID**: `DB-002`
- **Título**: Elaborar Modelo Lógico Relacional Normalizado (3FN)
- **Área**: Banco de Dados
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `DB-001` | ➡️ Próximo: `DB-003`
- **Dependências Diretas**: `DB-001`
- **Prioridade**: P0 | **Estimativa**: 5 SP | **Tipo**: feature
- **Objetivo**: Transformar o modelo conceitual em um modelo relacional normalizado até a 3ª Forma Normal, eliminando anomalias de inserção, atualização e exclusão.
- **Descrição**: Especificar chaves primárias (UUID v4), chaves estrangeiras com regras de integridade referencial (ON DELETE RESTRICT para histórico acadêmico), tipos primitivos e restrições de integridade.
- **História de Usuário**: Como Administrador de Banco de Dados, quero um modelo relacional normalizado, para garantir a consistência das notas e faltas dos estudantes.
- **Critérios de Aceitação**:
- Todas as tabelas em 3FN documentadas com tipos e constraints.
- Nenhuma informação de notas ou faltas duplicada entre módulos.
- Chaves compostas modeladas para tabelas associativas (ex: aluno-disciplina).
- **Definição de Pronto (DoD)**: Esquema relacional aprovado e pronto para transcrição em ORM.
- **Observações Técnicas**: Utilizar UUID v4 como PK para evitar ID enumeration e facilitar sincronização.

---

### [DB-003] Configurar Instância PostgreSQL 16 e Ambiente Docker Compose
- **ID**: `DB-003`
- **Título**: Configurar Instância PostgreSQL 16 e Ambiente Docker Compose
- **Área**: Banco de Dados
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `DB-002` | ➡️ Próximo: `DB-004`
- **Dependências Diretas**: `Nenhuma`
- **Prioridade**: P0 | **Estimativa**: 2 SP | **Tipo**: infraestrutura
- **Objetivo**: Disponibilizar um ambiente de banco de dados padronizado, reprodutível e isolado para todos os desenvolvedores da equipe via Docker.
- **Descrição**: Criar arquivo docker-compose.yml contendo serviço PostgreSQL 16 Alpine, volumes persistentes, timezone America/Sao_Paulo, porta padrão 5432 e credenciais parametrizadas via variáveis de ambiente.
- **História de Usuário**: Como Desenvolvedor do Time, quero subir o banco de dados com um único comando docker compose up -d, para iniciar o desenvolvimento local imediatamente sem conflitos de configuração.
- **Critérios de Aceitação**:
- docker-compose.yml funcional com PostgreSQL 16.
- Volume persistente mapeado para evitar perda de dados no reinício do container.
- Healthcheck configurado garantindo que o serviço responda ao comando pg_isready.
- **Definição de Pronto (DoD)**: Container sobe sem erros e aceita conexões externas autenticadas.
- **Observações Técnicas**: Não versionar senhas em texto puro; utilizar referências a .env.

---

### [DB-004] Inicializar Prisma ORM e Estrutura de Migrations Versionadas
- **ID**: `DB-004`
- **Título**: Inicializar Prisma ORM e Estrutura de Migrations Versionadas
- **Área**: Banco de Dados
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `DB-003` | ➡️ Próximo: `DB-005`
- **Dependências Diretas**: `DB-003`
- **Prioridade**: P0 | **Estimativa**: 2 SP | **Tipo**: infraestrutura
- **Objetivo**: Configurar o Prisma ORM no projeto para gerenciar o esquema de dados e versionamento seguro de alterações via migrations.
- **Descrição**: Inicializar a pasta prisma/, configurar o arquivo schema.prisma com o provider postgresql, definir o client generator e estruturar comandos no package.json para migração e geração de tipos.
- **História de Usuário**: Como Desenvolvedor Back-end, quero usar o Prisma para aplicar migrations de forma rastreável, para que todo o time compartilhe a mesma versão do banco.
- **Critérios de Aceitação**:
- schema.prisma criado apontando para a DATABASE_URL do .env.
- Scripts npm run db:migrate e npm run db:generate funcionando.
- Pasta prisma/migrations/ monitorada pelo git.
- **Definição de Pronto (DoD)**: Comando npx prisma migrate dev roda com sucesso contra o banco Docker.
- **Observações Técnicas**: Usar convenção snake_case nas colunas do banco com @map para manter camelCase no TypeScript.

---

### [DB-005] Criar Enumerações Globais de Sistema (Roles, Status, Graus de Risco)
- **ID**: `DB-005`
- **Título**: Criar Enumerações Globais de Sistema (Roles, Status, Graus de Risco)
- **Área**: Banco de Dados
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `DB-004` | ➡️ Próximo: `DB-006`
- **Dependências Diretas**: `DB-004`
- **Prioridade**: P0 | **Estimativa**: 1 SP | **Tipo**: feature
- **Objetivo**: Padronizar valores constantes de domínio no banco para garantir consistência de estados em todo o ciclo de vida da aplicação.
- **Descrição**: Criar enums no Prisma: Role (ADMIN, COORDINATOR, TEACHER, STUDENT), EnrollmentStatus (ACTIVE, COMPLETED, DROPPED, SUSPENDED), RiskLevel (LOW, MODERATE, HIGH, CRITICAL), SubmissionStatus (PENDING, SUBMITTED, EVALUATED, LATE) e HelpRequestStatus (OPEN, IN_PROGRESS, RESOLVED, CLOSED).
- **História de Usuário**: Como Engenheiro de Software, quero enums definidos no schema do banco, para evitar erros de digitação e garantir integridade nos filtros.
- **Critérios de Aceitação**:
- Enums criados e validados no schema.prisma.
- Migration gerada criando os tipos nativos enum no PostgreSQL.
- Tipos exportados compatíveis com as validações da API.
- **Definição de Pronto (DoD)**: Tipos enum gerados no Prisma Client e testados.
- **Observações Técnicas**: Enums nativos do Postgres garantem performance superior e rejeição imediata de valores inválidos.

---

### [DB-006] Implementar Tabela de Usuários (users) com Hash Seguro de Senha
- **ID**: `DB-006`
- **Título**: Implementar Tabela de Usuários (users) com Hash Seguro de Senha
- **Área**: Banco de Dados
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `DB-005` | ➡️ Próximo: `DB-007`
- **Dependências Diretas**: `DB-004, DB-005`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Criar a entidade central de autenticação do sistema com proteção de credenciais e identificador único universal.
- **Descrição**: Implementar a tabela users com colunas: id (UUID), email (único, indexado), password_hash (VARCHAR 255 para bcrypt/argon2), role (enum Role), is_active (BOOLEAN padrão true), created_at e updated_at.
- **História de Usuário**: Como Usuário do Sistema, quero ter uma conta segura no banco, para acessar o sistema com credenciais protegidas.
- **Critérios de Aceitação**:
- Tabela users com constraint UNIQUE em email.
- Campo password_hash não nulo sem armazenamento de texto puro.
- Índices criados no campo email.
- **Definição de Pronto (DoD)**: Migration aplicada e teste de inserção com e-mail duplicado rejeitado com erro P2002.
- **Observações Técnicas**: Armazenar e-mail em minúsculo (lowercased) para evitar duplicidade de caixa alta/baixa.

---

### [DB-007] Implementar Tabela de Perfis de Usuário (user_profiles) e Dados de Contato
- **ID**: `DB-007`
- **Título**: Implementar Tabela de Perfis de Usuário (user_profiles) e Dados de Contato
- **Área**: Banco de Dados
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `DB-006` | ➡️ Próximo: `DB-008`
- **Dependências Diretas**: `DB-006`
- **Prioridade**: P1 | **Estimativa**: 2 SP | **Tipo**: feature
- **Objetivo**: Separar dados de credenciais dos dados pessoais do estudante e professor, atendendo ao princípio de minimização da LGPD.
- **Descrição**: Criar a tabela user_profiles com: id (UUID), user_id (FK 1:1 única com users), full_name, registration_number (matrícula SENAI única), phone, avatar_url, bio, created_at e updated_at.
- **História de Usuário**: Como Administrador, quero vincular um perfil institucional ao login do usuário, para identificar estudantes e instrutores por nome e matrícula.
- **Critérios de Aceitação**:
- Relacionamento 1:1 entre users e user_profiles com cascade delete.
- registration_number único no sistema.
- Campos pessoais isolados facilitando futuras rotinas de anonimização LGPD.
- **Definição de Pronto (DoD)**: Schema gerado e verificado com integridade 1:1.
- **Observações Técnicas**: Índices no campo registration_number para agilizar buscas da secretaria.

---

### [DB-008] Criar Tabela de Sessões e Refresh Tokens com Revogação (auth_sessions)
- **ID**: `DB-008`
- **Título**: Criar Tabela de Sessões e Refresh Tokens com Revogação (auth_sessions)
- **Área**: Banco de Dados
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `DB-007` | ➡️ Próximo: `DB-009`
- **Dependências Diretas**: `DB-006`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Permitir renovação segura de tokens JWT com rastreamento de dispositivos e invalidação imediata em caso de logout ou suspeita de vazamento.
- **Descrição**: Criar tabela auth_sessions contendo: id (UUID), user_id (FK), refresh_token_hash (único), user_agent, ip_address, expires_at, is_revoked (padrão false) e created_at.
- **História de Usuário**: Como Aluno ou Professor, quero poder desconectar de sessões antigas ou roubadas, para proteger minha privacidade acadêmica.
- **Critérios de Aceitação**:
- Tabela criada com chave estrangeira para users(id).
- Campo is_revoked indexado para consulta ultra-rápida no middleware de auth.
- Constraint de expiração verificável.
- **Definição de Pronto (DoD)**: Migration criada com índices eficientes em refresh_token_hash.
- **Observações Técnicas**: O token nunca é salvo puro, apenas o hash SHA-256 do mesmo.

---

### [DB-009] Implementar Tabela de Registro de Atividades e Auditoria (audit_logs)
- **ID**: `DB-009`
- **Título**: Implementar Tabela de Registro de Atividades e Auditoria (audit_logs)
- **Área**: Banco de Dados
- **Epic**: EPIC-10: Relatórios, Governança de Dados & Qualidade
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `DB-008` | ➡️ Próximo: `DB-010`
- **Dependências Diretas**: `DB-006`
- **Prioridade**: P1 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Registrar alterações críticas no sistema (alteração de notas, lançamento de faltas, visualização de notas pedagógicas confidenciais).
- **Descrição**: Criar tabela audit_logs com: id (UUID), user_id (FK nula em ações de sistema), action (VARCHAR), entity (ex: 'Grade', 'PedagogicalNote'), entity_id (VARCHAR), old_values (JSONB), new_values (JSONB), ip_address, created_at.
- **História de Usuário**: Como Coordenador Pedagógico, quero auditoria de modificações em notas e frequências, para garantir total transparência e conformidade acadêmica.
- **Critérios de Aceitação**:
- Tabela com campos JSONB para armazenar diff de valores antigos e novos.
- Sem foreign key estrita com deleção em cascata (manter histórico mesmo se usuário for deletado).
- Índice temporal em created_at para relatórios rápidos.
- **Definição de Pronto (DoD)**: Migration executada e teste de inserção de JSONB validado.
- **Observações Técnicas**: Usar tipo JSONB do Postgres para possibilitar buscas indexadas com @> se necessário.

---

### [DB-010] Criar Script Base de Migração Inicial e Verificação de Conexão
- **ID**: `DB-010`
- **Título**: Criar Script Base de Migração Inicial e Verificação de Conexão
- **Área**: Banco de Dados
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `DB-009` | ➡️ Próximo: `DB-011`
- **Dependências Diretas**: `DB-001 até DB-009`
- **Prioridade**: P0 | **Estimativa**: 2 SP | **Tipo**: teste
- **Objetivo**: Consolidar o primeiro ciclo de migrações (Lote 1) com script de teste de conectividade e sanidade das tabelas de autenticação.
- **Descrição**: Criar script Node.js / TypeScript prisma/check-connection.ts que executa uma query de sanidade (SELECT 1), valida a presença das tabelas criadas no Lote 1 e exibe o status no terminal.
- **História de Usuário**: Como Tech Lead, quero um verificador de integridade do banco no Lote 1, para assegurar que a fundação esteja sólida antes de avançar para a estrutura acadêmica.
- **Critérios de Aceitação**:
- Script executa e retorna código 0 quando o banco está saudável.
- Verifica a criação das 4 tabelas fundamentais (users, user_profiles, auth_sessions, audit_logs).
- Documentado no README do projeto.
- **Definição de Pronto (DoD)**: Execução com sucesso em ambiente local do desenvolvedor.
- **Observações Técnicas**: Esse script será acoplado aos hooks de CI no futuro.

---

### [DB-011] Implementar Tabela de Cursos Técnicos (courses)
- **ID**: `DB-011`
- **Título**: Implementar Tabela de Cursos Técnicos (courses)
- **Área**: Banco de Dados
- **Epic**: EPIC-02: Gestão Acadêmica & Estrutura SENAI
- **Lote / Sprint**: Lote 2 (S2)
- **Sequência na Squad**: ⬅️ Anterior: `DB-010` | ➡️ Próximo: `DB-012`
- **Dependências Diretas**: `DB-004`
- **Prioridade**: P0 | **Estimativa**: 2 SP | **Tipo**: feature
- **Objetivo**: Modelar e persistir os cursos oferecidos pela unidade SENAI (ex: Técnico em Mecânica, Eletromecânica, ADS).
- **Descrição**: Criar tabela courses com: id (UUID), code (código SENAI único, ex: TEC-MEC-01), name (VARCHAR 150), description (TEXT), total_hours (INTEGER), is_active (BOOLEAN), created_at e updated_at.
- **História de Usuário**: Como Secretaria Acadêmica, quero cadastrar os cursos técnicos ofertados, para estruturar as turmas e matrizes curriculares.
- **Critérios de Aceitação**:
- Código do curso único (UNIQUE).
- Validação de total_hours maior que zero.
- Soft delete ou flag is_active para preservação de histórico.
- **Definição de Pronto (DoD)**: Tabela courses criada com migration e tipos TypeScript atualizados no Prisma.
- **Observações Técnicas**: Cursos não devem ser excluídos fisicamente se possuírem turmas associadas.

---

### [DB-012] Implementar Tabela de Turmas Acadêmicas (classes)
- **ID**: `DB-012`
- **Título**: Implementar Tabela de Turmas Acadêmicas (classes)
- **Área**: Banco de Dados
- **Epic**: EPIC-02: Gestão Acadêmica & Estrutura SENAI
- **Lote / Sprint**: Lote 2 (S2)
- **Sequência na Squad**: ⬅️ Anterior: `DB-011` | ➡️ Próximo: `DB-013`
- **Dependências Diretas**: `DB-011`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Modelar as turmas letivas vinculadas a um curso técnico e período letivo.
- **Descrição**: Criar tabela classes com: id (UUID), course_id (FK courses), code (ex: MEC-2026-1T), period (VARCHAR 20, ex: '2026.1'), shift (enum Shift: MORNING, AFTERNOON, NIGHT), max_students (INTEGER), status (enum ClassStatus: PLANNING, ACTIVE, COMPLETED, ARCHIVED), start_date, end_date.
- **História de Usuário**: Como Coordenador, quero registrar as turmas do semestre, para alocar docentes e matricular estudantes.
- **Critérios de Aceitação**:
- Chave estrangeira para courses com ON DELETE RESTRICT.
- Restrição de unicidade em code por período letivo.
- Constraint verificando start_date < end_date.
- **Definição de Pronto (DoD)**: Migration criada com integridade referencial testada.
- **Observações Técnicas**: Índice composto em (course_id, period) para consultas frequentes de turmas do semestre.

---

### [DB-013] Criar Tabela de Disciplinas Teórico-Práticas (subjects)
- **ID**: `DB-013`
- **Título**: Criar Tabela de Disciplinas Teórico-Práticas (subjects)
- **Área**: Banco de Dados
- **Epic**: EPIC-02: Gestão Acadêmica & Estrutura SENAI
- **Lote / Sprint**: Lote 2 (S2)
- **Sequência na Squad**: ⬅️ Anterior: `DB-012` | ➡️ Próximo: `DB-014`
- **Dependências Diretas**: `DB-011`
- **Prioridade**: P0 | **Estimativa**: 2 SP | **Tipo**: feature
- **Objetivo**: Estruturar as unidades curriculares que compõem o curso técnico SENAI.
- **Descrição**: Criar tabela subjects com: id (UUID), course_id (FK courses), name (ex: 'Metrologia Dimensional', 'Processos de Fabricação Mecânica'), code (VARCHAR 50), workload_hours (INTEGER), syllabus (TEXT) e is_active (BOOLEAN).
- **História de Usuário**: Como Coordenador Pedagógico, quero cadastrar as disciplinas da matriz, para associar módulos práticos e planos de aula.
- **Critérios de Aceitação**:
- Disciplina vinculada obrigatoriamente a um curso.
- Carga horária estritamente positiva.
- Índice em name para pesquisas autocompletar.
- **Definição de Pronto (DoD)**: Tabela subjects criada e testada no Prisma Studio.
- **Observações Técnicas**: Tratar equivalências curriculares futuramente por tabela associativa de pré-requisitos.

---

### [DB-014] Implementar Tabela de Módulos de Aprendizagem Prática SENAI (learning_modules)
- **ID**: `DB-014`
- **Título**: Implementar Tabela de Módulos de Aprendizagem Prática SENAI (learning_modules)
- **Área**: Banco de Dados
- **Epic**: EPIC-02: Gestão Acadêmica & Estrutura SENAI
- **Lote / Sprint**: Lote 2 (S2)
- **Sequência na Squad**: ⬅️ Anterior: `DB-013` | ➡️ Próximo: `DB-015`
- **Dependências Diretas**: `DB-013`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Modelar a estrutura modular prática característica do SENAI (ex: Módulo de Tornearia Cilíndrica, Metrologia com Micrômetro).
- **Descrição**: Criar tabela learning_modules com: id (UUID), subject_id (FK subjects), title (VARCHAR 120), order_index (INTEGER), description (TEXT), practical_hours (INTEGER), passing_score (DECIMAL 4,2 padrão 6.00).
- **História de Usuário**: Como Professor de Oficina, quero organizar o ensino em módulos práticos sequenciais, para avaliar o progresso gradual dos estudantes na bancada.
- **Critérios de Aceitação**:
- Módulo associado a uma disciplina (FK com cascade).
- order_index garantindo a sequência didática recomendada.
- passing_score com validação entre 0.00 e 10.00.
- **Definição de Pronto (DoD)**: Tabela learning_modules funcional e integrada ao schema Prisma.
- **Observações Técnicas**: Permitir que módulos tenham pesos ponderados diferentes na composição final da disciplina.

---

### [DB-015] Criar Tabela de Competências e Habilidades Técnicas (competencies)
- **ID**: `DB-015`
- **Título**: Criar Tabela de Competências e Habilidades Técnicas (competencies)
- **Área**: Banco de Dados
- **Epic**: EPIC-04: Atividades Práticas de Oficina & Competências
- **Lote / Sprint**: Lote 2 (S2)
- **Sequência na Squad**: ⬅️ Anterior: `DB-014` | ➡️ Próximo: `DB-016`
- **Dependências Diretas**: `DB-005`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Cadastrar a taxonomia de competências técnicas requeridas pelo perfil profissional SENAI.
- **Descrição**: Criar tabela competencies com: id (UUID), code (ex: 'COMP-MET-01'), title (ex: 'Medição com Paquímetro e Tolerância H7'), category (enum CompetencyCategory: TECHNICAL, SAFETY, PROCEDURAL), description (TEXT).
- **História de Usuário**: Como Coordenador de Ensino, quero cadastrar as competências técnicas obrigatórias, para avaliar a proficiência dos estudantes segundo padrões industriais.
- **Critérios de Aceitação**:
- Código da competência único.
- Categorias de competência bem definidas via enum.
- Campos informativos prontos para exibição nos dashboards de radar.
- **Definição de Pronto (DoD)**: Tabela competencies migrada no Postgres.
- **Observações Técnicas**: Essa tabela é a base para a autoavaliação do aluno e a avaliação prática do professor.

---

### [DB-016] Modelar Relacionamento Módulo-Competência (module_competencies)
- **ID**: `DB-016`
- **Título**: Modelar Relacionamento Módulo-Competência (module_competencies)
- **Área**: Banco de Dados
- **Epic**: EPIC-04: Atividades Práticas de Oficina & Competências
- **Lote / Sprint**: Lote 2 (S2)
- **Sequência na Squad**: ⬅️ Anterior: `DB-015` | ➡️ Próximo: `DB-017`
- **Dependências Diretas**: `DB-014, DB-015`
- **Prioridade**: P0 | **Estimativa**: 2 SP | **Tipo**: feature
- **Objetivo**: Estabelecer a relação N:M entre módulos práticos e as competências técnicas desenvolvidas.
- **Descrição**: Criar tabela associativa module_competencies com: module_id (FK learning_modules), competency_id (FK competencies), weight (DECIMAL 3,2 padrão 1.00), required_level (INTEGER 1-5). Chave primária composta (module_id, competency_id).
- **História de Usuário**: Como Professor de Oficina, quero vincular quais competências são treinadas em cada módulo, para medir a evolução técnica do estudante.
- **Critérios de Aceitação**:
- Chave primária composta impedindo duplicações.
- FKs com exclusão em cascata se o módulo for removido.
- Nível requerido delimitado entre 1 (Básico) e 5 (Avançado).
- **Definição de Pronto (DoD)**: Relação N:M modelada e validada com seed preliminar.
- **Observações Técnicas**: Permite ponderar quais habilidades têm maior impacto na nota do módulo.

---

### [DB-017] Implementar Tabela de Matrículas de Estudantes (enrollments)
- **ID**: `DB-017`
- **Título**: Implementar Tabela de Matrículas de Estudantes (enrollments)
- **Área**: Banco de Dados
- **Epic**: EPIC-02: Gestão Acadêmica & Estrutura SENAI
- **Lote / Sprint**: Lote 2 (S2)
- **Sequência na Squad**: ⬅️ Anterior: `DB-016` | ➡️ Próximo: `DB-018`
- **Dependências Diretas**: `DB-006, DB-012`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Registrar formalmente o ingresso e status de um estudante em uma turma específica.
- **Descrição**: Criar tabela enrollments com: id (UUID), student_id (FK users com role STUDENT), class_id (FK classes), enrollment_date (DATE), status (enum EnrollmentStatus), final_grade (DECIMAL 4,2), attendance_rate (DECIMAL 5,2), created_at e updated_at.
- **História de Usuário**: Como Secretaria, quero matricular estudantes em turmas, para que eles acessem o portal e acompanhem suas aulas.
- **Critérios de Aceitação**:
- Um estudante só pode ter uma matrícula ativa por turma (UNIQUE em student_id, class_id).
- FK com validação de perfil (apenas usuários com role STUDENT).
- Status padrão ACTIVE.
- **Definição de Pronto (DoD)**: Tabela enrollments implementada com restrição de unicidade composta.
- **Observações Técnicas**: attendance_rate armazenado em porcentagem (0.00 a 100.00) com índice para filtros de risco.

---

### [DB-018] Modelar Associação de Professores a Disciplinas e Turmas (teacher_assignments)
- **ID**: `DB-018`
- **Título**: Modelar Associação de Professores a Disciplinas e Turmas (teacher_assignments)
- **Área**: Banco de Dados
- **Epic**: EPIC-02: Gestão Acadêmica & Estrutura SENAI
- **Lote / Sprint**: Lote 2 (S2)
- **Sequência na Squad**: ⬅️ Anterior: `DB-017` | ➡️ Próximo: `DB-019`
- **Dependências Diretas**: `DB-006, DB-012, DB-013`
- **Prioridade**: P0 | **Estimativa**: 2 SP | **Tipo**: feature
- **Objetivo**: Vincular instrutores às turmas e matérias que ministram, estabelecendo a permissão de lançamento de notas e faltas.
- **Descrição**: Criar tabela teacher_assignments com: id (UUID), teacher_id (FK users com role TEACHER), class_id (FK classes), subject_id (FK subjects), assigned_at, is_main_teacher (BOOLEAN).
- **História de Usuário**: Como Coordenador, quero atribuir professores às turmas, para conceder permissão de diário aos docentes responsáveis.
- **Critérios de Aceitação**:
- Chave composta UNIQUE (teacher_id, class_id, subject_id).
- Foreign keys íntegras com ON DELETE RESTRICT.
- Facilita autorização no backend (RBAC contextual).
- **Definição de Pronto (DoD)**: Tabela de atribuição criada com índices eficientes para checagem de autorização.
- **Observações Técnicas**: Permite múltiplos professores por disciplina (ex: teoria e prática de oficina com instrutores diferentes).

---

### [DB-019] Configurar Constraints de Unicidade e Integridade Acadêmica em Matrículas
- **ID**: `DB-019`
- **Título**: Configurar Constraints de Unicidade e Integridade Acadêmica em Matrículas
- **Área**: Banco de Dados
- **Epic**: EPIC-02: Gestão Acadêmica & Estrutura SENAI
- **Lote / Sprint**: Lote 2 (S2)
- **Sequência na Squad**: ⬅️ Anterior: `DB-018` | ➡️ Próximo: `DB-020`
- **Dependências Diretas**: `DB-017`
- **Prioridade**: P0 | **Estimativa**: 2 SP | **Tipo**: feature
- **Objetivo**: Garantir no nível de banco de dados que regras acadêmicas críticas não sejam violadas por concorrência ou falhas de aplicação.
- **Descrição**: Aplicar constraints de verificação (CHECK constraints): notas finais entre 0.00 e 10.00; frequência entre 0.00 e 100.00; datas de início anterior a término; capacidade máxima de alunos na turma respeitada.
- **História de Usuário**: Como Administrador de Banco de Dados, quero regras CHECK rígidas, para impedir que notas impossíveis ou estados inconsistentes sejam gravados.
- **Critérios de Aceitação**:
- CHECK constraints ativas no PostgreSQL.
- Tentativas de inserir nota 10.50 ou frequência -5% falham com erro de constraint.
- Documentação das constraints registrada no schema.
- **Definição de Pronto (DoD)**: Script de constraints executado e validado com testes de violação proposital.
- **Observações Técnicas**: Prisma suporta @@check no PostgreSQL nativo a partir das versões recentes.

---

### [DB-020] Criar Seed de Estrutura Curricular SENAI (Mecânica e Metrologia)
- **ID**: `DB-020`
- **Título**: Criar Seed de Estrutura Curricular SENAI (Mecânica e Metrologia)
- **Área**: Banco de Dados
- **Epic**: EPIC-02: Gestão Acadêmica & Estrutura SENAI
- **Lote / Sprint**: Lote 2 (S2)
- **Sequência na Squad**: ⬅️ Anterior: `DB-019` | ➡️ Próximo: `DB-021`
- **Dependências Diretas**: `DB-011, DB-012, DB-013, DB-014, DB-015, DB-016, DB-017, DB-018`
- **Prioridade**: P1 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Popular o banco de dados local com uma grade completa e realista de curso técnico SENAI para alimentar o desenvolvimento do front e back.
- **Descrição**: Criar script prisma/seed.ts que popula: Curso Técnico em Mecânica Industrial, 2 turmas (MEC-2026-1 e MEC-2026-2), 4 disciplinas (Metrologia, Desenho Técnico Mecânico, Usinagem Convencional, Segurança do Trabalho), 8 módulos práticos e 15 competências industriais.
- **História de Usuário**: Como Desenvolvedor, quero rodar npm run db:seed e ter uma escola SENAI simulada pronta para testes, para agilizar a validação de telas e rotas.
- **Critérios de Aceitação**:
- Script roda de forma idempotente (upsert) sem duplicar dados.
- Cria turmas e disciplinas com dados coerentes do SENAI.
- Vincula competências reais aos módulos.
- **Definição de Pronto (DoD)**: npm run db:seed popula o banco sem erros e pode ser reexecutado com segurança.
- **Observações Técnicas**: Dados completamente anônimos e fictícios, sem dados pessoais reais.

---

### [DB-021] Implementar Tabela de Aulas Ministradas e Diário de Bordo (class_lessons)
- **ID**: `DB-021`
- **Título**: Implementar Tabela de Aulas Ministradas e Diário de Bordo (class_lessons)
- **Área**: Banco de Dados
- **Epic**: EPIC-03: Diário de Classe: Notas & Frequência
- **Lote / Sprint**: Lote 3 (S3)
- **Sequência na Squad**: ⬅️ Anterior: `DB-020` | ➡️ Próximo: `DB-022`
- **Dependências Diretas**: `DB-012, DB-013, DB-014, DB-018`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Persistir os encontros letivos e aulas práticas ministradas em cada turma, módulo e disciplina.
- **Descrição**: Criar tabela class_lessons com: id (UUID), class_id (FK classes), subject_id (FK subjects), module_id (FK learning_modules opcional), teacher_id (FK users), lesson_date (DATE), workload_hours (INTEGER padrão 4), topic_summary (TEXT), lab_environment (VARCHAR 100, ex: 'Oficina de Tornearia 02') e created_at.
- **História de Usuário**: Como Professor, quero registrar cada aula ministrada com seu conteúdo e oficina utilizada, para vincular a chamada de frequência da turma.
- **Critérios de Aceitação**:
- FKs íntegras para classes, subjects, learning_modules e users.
- Índice composto em (class_id, subject_id, lesson_date) para listagem cronológica rápida.
- Validação de workload_hours entre 1 e 8 horas por turno.
- **Definição de Pronto (DoD)**: Migration de class_lessons criada e testada com inserção vinculada a módulo prático.
- **Observações Técnicas**: Serve de âncora obrigatória para os registros de presença (DB-022) e endpoint de diário (BE-021).

---

### [DB-022] Implementar Tabela de Registros de Presença e Faltas (attendance_records)
- **ID**: `DB-022`
- **Título**: Implementar Tabela de Registros de Presença e Faltas (attendance_records)
- **Área**: Banco de Dados
- **Epic**: EPIC-03: Diário de Classe: Notas & Frequência
- **Lote / Sprint**: Lote 3 (S3)
- **Sequência na Squad**: ⬅️ Anterior: `DB-021` | ➡️ Próximo: `DB-023`
- **Dependências Diretas**: `DB-017, DB-021`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Armazenar a frequência individual de cada estudante em cada aula ministrada com suporte a chamada em 1 clique.
- **Descrição**: Criar tabela attendance_records com: id (UUID), lesson_id (FK class_lessons), enrollment_id (FK enrollments), student_id (FK users), status (enum AttendanceStatus: PRESENT, ABSENT, LATE, JUSTIFIED), absent_hours (INTEGER padrão 0), justification_note (TEXT opcional) e recorded_at.
- **História de Usuário**: Como Professor, quero que a presença ou falta de cada aluno fique gravada por aula sem duplicidade, para automatizar o cálculo do limite de 75% de frequência.
- **Critérios de Aceitação**:
- Constraint UNIQUE composta em (lesson_id, student_id) impedindo chamada duplicada na mesma aula.
- Chave estrangeira ligada a enrollments garantindo que apenas alunos matriculados na turma recebam presença.
- Índice em (student_id, status) para agregação instantânea de faltas.
- **Definição de Pronto (DoD)**: Tabela attendance_records migrada e validada com upsert em lote.
- **Observações Técnicas**: Consumida diretamente pelo endpoint de chamada em lote (BE-022) e tela de chamada (FE-022).

---

### [DB-023] Implementar Tabela de Tarefas e Atividades Práticas (practical_tasks)
- **ID**: `DB-023`
- **Título**: Implementar Tabela de Tarefas e Atividades Práticas (practical_tasks)
- **Área**: Banco de Dados
- **Epic**: EPIC-04: Atividades Práticas de Oficina & Competências
- **Lote / Sprint**: Lote 3 (S3)
- **Sequência na Squad**: ⬅️ Anterior: `DB-022` | ➡️ Próximo: `DB-024`
- **Dependências Diretas**: `DB-012, DB-014, DB-016`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Modelar as atividades práticas de bancada e usinagem associadas aos módulos técnicos SENAI.
- **Descrição**: Criar tabela practical_tasks com: id (UUID), module_id (FK learning_modules), class_id (FK classes), title (ex: 'Usinagem de Eixo Escalonado Ø25mm H7'), description (TEXT), blueprint_url (link do desenho técnico), due_date (TIMESTAMP), max_score (DECIMAL 4,2 padrão 10.00), is_mandatory (BOOLEAN).
- **História de Usuário**: Como Instrutor de Oficina, quero cadastrar as peças e exercícios práticos do módulo, para acompanhar quem já concluiu cada etapa na máquina.
- **Critérios de Aceitação**:
- Tarefa vinculada a um módulo prático (learning_modules) e turma (classes).
- Campo max_score validado entre 1.00 e 10.00.
- Índice por (class_id, due_date) para consulta rápida de pendências.
- **Definição de Pronto (DoD)**: Tabela practical_tasks criada no Prisma e migrada no PostgreSQL.
- **Observações Técnicas**: Base para BE-024 (criação de tarefa prática) e FE-024 (painel de oficinas).

---

### [DB-024] Criar Tabela de Critérios de Avaliação Prática / Rubricas (task_criteria)
- **ID**: `DB-024`
- **Título**: Criar Tabela de Critérios de Avaliação Prática / Rubricas (task_criteria)
- **Área**: Banco de Dados
- **Epic**: EPIC-04: Atividades Práticas de Oficina & Competências
- **Lote / Sprint**: Lote 3 (S3)
- **Sequência na Squad**: ⬅️ Anterior: `DB-023` | ➡️ Próximo: `DB-025`
- **Dependências Diretas**: `DB-015, DB-023`
- **Prioridade**: P1 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Estruturar os critérios técnicos objetivos (tolerância dimensional, rugosidade, uso de EPI) de cada atividade prática.
- **Descrição**: Criar tabela task_criteria com: id (UUID), task_id (FK practical_tasks com cascade), competency_id (FK competencies), criterion_name (ex: 'Tolerância Dimensional ±0,02mm no Micrômetro'), weight (DECIMAL 3,2), min_acceptable_level (INTEGER 1-5).
- **História de Usuário**: Como Professor, quero decompor a avaliação de uma peça prática em critérios claros ligados às competências, para tornar a nota técnica e justa.
- **Critérios de Aceitação**:
- Cada critério referencia uma tarefa prática e uma competência técnica oficial.
- Soma ou ponderação de pesos suportada para cálculo automático.
- Exclusão em cascata caso a tarefa ainda não possua entregas avaliadas.
- **Definição de Pronto (DoD)**: Tabela task_criteria migrada e testada com rubricas de Metrologia e Tornearia.
- **Observações Técnicas**: Suporta o modal de avaliação por rubricas no frontend (FE-026) e endpoint BE-025.

---

### [DB-025] Implementar Tabela de Submissões e Entregas Práticas (task_submissions)
- **ID**: `DB-025`
- **Título**: Implementar Tabela de Submissões e Entregas Práticas (task_submissions)
- **Área**: Banco de Dados
- **Epic**: EPIC-04: Atividades Práticas de Oficina & Competências
- **Lote / Sprint**: Lote 3 (S3)
- **Sequência na Squad**: ⬅️ Anterior: `DB-024` | ➡️ Próximo: `DB-026`
- **Dependências Diretas**: `DB-017, DB-023`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Controlar o estado de entrega e execução de cada atividade prática por estudante.
- **Descrição**: Criar tabela task_submissions com: id (UUID), task_id (FK practical_tasks), student_id (FK users), enrollment_id (FK enrollments), status (enum SubmissionStatus: PENDING, SUBMITTED, EVALUATED, LATE), completed_at (TIMESTAMP), evidence_url (VARCHAR), student_notes (TEXT), final_task_score (DECIMAL 4,2).
- **História de Usuário**: Como Aluno ou Professor, quero saber exatamente quais tarefas práticas estão pendentes, entregues, atrasadas ou avaliadas.
- **Critérios de Aceitação**:
- Constraint UNIQUE em (task_id, student_id).
- Índices em (student_id, status) para alimentar a lista de pendências do portal do aluno.
- Integridade com enrollments assegurando vínculo ativo na turma.
- **Definição de Pronto (DoD)**: Tabela task_submissions migrada e validada com estados de transição.
- **Observações Técnicas**: Alimenta diretamente BE-025, BE-026, FE-025 e FE-036 (painel de pendências do aluno).

---

### [DB-026] Criar Tabela de Avaliações por Rubrica dos Professores (submission_evaluations)
- **ID**: `DB-026`
- **Título**: Criar Tabela de Avaliações por Rubrica dos Professores (submission_evaluations)
- **Área**: Banco de Dados
- **Epic**: EPIC-04: Atividades Práticas de Oficina & Competências
- **Lote / Sprint**: Lote 3 (S3)
- **Sequência na Squad**: ⬅️ Anterior: `DB-025` | ➡️ Próximo: `DB-027`
- **Dependências Diretas**: `DB-024, DB-025`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Registrar a nota e o nível de domínio atribuído pelo professor em cada critério/rubrica de uma entrega prática.
- **Descrição**: Criar tabela submission_evaluations com: id (UUID), submission_id (FK task_submissions), criterion_id (FK task_criteria), evaluator_id (FK users role TEACHER), achieved_level (INTEGER 1-5), score_awarded (DECIMAL 4,2), technical_feedback (TEXT) e evaluated_at (TIMESTAMP).
- **História de Usuário**: Como Professor, quero gravar o desempenho do aluno em cada rubrica da peça usinada, gerando evidência concreta de evolução da competência.
- **Critérios de Aceitação**:
- Constraint UNIQUE em (submission_id, criterion_id).
- Validação CHECK para achieved_level entre 1 e 5.
- FK para evaluator_id identificando o docente avaliador.
- **Definição de Pronto (DoD)**: Migration aplicada e testada com cálculo de nota consolidada da submissão.
- **Observações Técnicas**: Fornece os dados reais para comparar com a autoavaliação do aluno (DB-038 / BE-037).

---

### [DB-027] Implementar Tabela de Avaliações Formativas e Provas (academic_assessments)
- **ID**: `DB-027`
- **Título**: Implementar Tabela de Avaliações Formativas e Provas (academic_assessments)
- **Área**: Banco de Dados
- **Epic**: EPIC-03: Diário de Classe: Notas & Frequência
- **Lote / Sprint**: Lote 3 (S3)
- **Sequência na Squad**: ⬅️ Anterior: `DB-026` | ➡️ Próximo: `DB-028`
- **Dependências Diretas**: `DB-012, DB-013, DB-014`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Cadastrar avaliações teóricas, microavaliações e provas aplicadas por disciplina e módulo.
- **Descrição**: Criar tabela academic_assessments com: id (UUID), class_id (FK classes), subject_id (FK subjects), module_id (FK learning_modules opcional), title (ex: 'Prova Teórica de Leitura de Paquímetro e Micrômetro'), assessment_type (enum: EXAM, MICRO_EVALUATION, PROJECT), weight (DECIMAL 3,2), application_date (DATE), max_grade (DECIMAL 4,2 padrão 10.00).
- **História de Usuário**: Como Professor, quero cadastrar provas e microavaliações com seus pesos, para compor a média do módulo junto com as práticas de oficina.
- **Critérios de Aceitação**:
- Peso (weight) estritamente maior que zero.
- Vinculação obrigatória a turma e disciplina.
- Ordenação por application_date.
- **Definição de Pronto (DoD)**: Tabela academic_assessments criada e integrada ao schema Prisma.
- **Observações Técnicas**: Utilizada pelos endpoints de lançamento de notas (BE-027) e tela de notas (FE-027).

---

### [DB-028] Implementar Tabela de Notas e Menções Finais (student_grades)
- **ID**: `DB-028`
- **Título**: Implementar Tabela de Notas e Menções Finais (student_grades)
- **Área**: Banco de Dados
- **Epic**: EPIC-03: Diário de Classe: Notas & Frequência
- **Lote / Sprint**: Lote 3 (S3)
- **Sequência na Squad**: ⬅️ Anterior: `DB-027` | ➡️ Próximo: `DB-029`
- **Dependências Diretas**: `DB-017, DB-027`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Armazenar as notas obtidas por cada estudante nas avaliações formativas e provas, com rastreabilidade de lançamentos.
- **Descrição**: Criar tabela student_grades com: id (UUID), assessment_id (FK academic_assessments), enrollment_id (FK enrollments), student_id (FK users), recorded_by (FK users role TEACHER), grade_value (DECIMAL 4,2), recovery_grade (DECIMAL 4,2 opcional), comments (TEXT), created_at e updated_at.
- **História de Usuário**: Como Aluno e Professor, queremos consultar as notas individuais e de recuperação de cada avaliação com precisão de duas casas decimais.
- **Critérios de Aceitação**:
- Constraint UNIQUE em (assessment_id, student_id).
- CHECK constraint garantindo grade_value e recovery_grade entre 0.00 e 10.00.
- Vínculo obrigatório com enrollment_id válido.
- **Definição de Pronto (DoD)**: Tabela student_grades migrada e validada com testes de limites numéricos.
- **Observações Técnicas**: Qualquer alteração posterior em nota já publicada dispara log em audit_logs (DB-009 / BE-048).

---

### [DB-029] Configurar Triggers / Funções para Validação de Período Letivo Fechado
- **ID**: `DB-029`
- **Título**: Configurar Triggers / Funções para Validação de Período Letivo Fechado
- **Área**: Banco de Dados
- **Epic**: EPIC-03: Diário de Classe: Notas & Frequência
- **Lote / Sprint**: Lote 3 (S3)
- **Sequência na Squad**: ⬅️ Anterior: `DB-028` | ➡️ Próximo: `DB-030`
- **Dependências Diretas**: `DB-012, DB-022, DB-025, DB-028`
- **Prioridade**: P1 | **Estimativa**: 5 SP | **Tipo**: feature
- **Objetivo**: Impedir no próprio banco de dados que notas ou presenças sejam alteradas caso a turma já esteja com status COMPLETED ou ARCHIVED.
- **Descrição**: Criar função PL/pgSQL fn_prevent_closed_class_mutation() e triggers associadas às tabelas student_grades, attendance_records e task_submissions que verificam o status da turma antes de permitir UPDATE ou DELETE.
- **História de Usuário**: Como Coordenador Acadêmico, quero garantia absoluta de que diários de turmas encerradas não sofram alterações retroativas não autorizadas.
- **Critérios de Aceitação**:
- Trigger bloqueia UPDATE/DELETE em notas e faltas quando classes.status IN ('COMPLETED', 'ARCHIVED').
- Lança exceção SQL clara identificável pelo backend (BE-029).
- Permite leitura (SELECT) normalmente para histórico.
- **Definição de Pronto (DoD)**: Migration SQL customizada aplicada e testada tentando alterar nota de turma fechada.
- **Observações Técnicas**: Trabalha em defesa em profundidade junto com o middleware de bloqueio (BE-029).

---

### [DB-030] Criar Seed com Registro Realista de Frequências e Notas Parciais
- **ID**: `DB-030`
- **Título**: Criar Seed com Registro Realista de Frequências e Notas Parciais
- **Área**: Banco de Dados
- **Epic**: EPIC-03: Diário de Classe: Notas & Frequência
- **Lote / Sprint**: Lote 3 (S3)
- **Sequência na Squad**: ⬅️ Anterior: `DB-029` | ➡️ Próximo: `DB-031`
- **Dependências Diretas**: `DB-020, DB-021, DB-022, DB-025, DB-026, DB-028`
- **Prioridade**: P1 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Popular o banco de desenvolvimento com histórico realista de aulas, chamadas, entregas práticas e notas de 30 estudantes fictícios.
- **Descrição**: Estender prisma/seed.ts para criar 30 alunos matriculados nas turmas de Mecânica, 12 aulas ministradas, registros de presença variados (alunos com 100%, 80% e alunos em risco com 68% de presença), 6 tarefas práticas de oficina e notas parciais.
- **História de Usuário**: Como Desenvolvedor Front-end e Back-end, quero dados realistas de notas e faltas no seed, para testar gráficos, médias e alertas de risco imediatamente.
- **Critérios de Aceitação**:
- Cria cenários reais: alunos com ótimo desempenho, alunos com entregas atrasadas e alunos próximos ao limite de faltas (25%).
- Execução idempotente integrada ao comando npm run db:seed.
- Zero uso de CPFs ou nomes de alunos reais.
- **Definição de Pronto (DoD)**: Seed executado gerando massa de dados completa para o Lote 3 e Lote 4.
- **Observações Técnicas**: Garante que os Dashboards (FE-031 a FE-038) já abram preenchidos com dados ricos.

---

### [DB-031] Implementar Tabela de Formulários de Autoavaliação (self_assessment_forms)
- **ID**: `DB-031`
- **Título**: Implementar Tabela de Formulários de Autoavaliação (self_assessment_forms)
- **Área**: Banco de Dados
- **Epic**: EPIC-07: Autoavaliação & Motor de Diagnóstico Explicável
- **Lote / Sprint**: Lote 4 (S4)
- **Sequência na Squad**: ⬅️ Anterior: `DB-030` | ➡️ Próximo: `DB-032`
- **Dependências Diretas**: `DB-012, DB-014, DB-016`
- **Prioridade**: P1 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Estruturar os ciclos e questionários de autoavaliação de competências práticas por módulo.
- **Descrição**: Criar tabela self_assessment_forms com: id (UUID), module_id (FK learning_modules), class_id (FK classes), title (VARCHAR 150), instructions (TEXT), opens_at (TIMESTAMP), closes_at (TIMESTAMP), is_active (BOOLEAN) e created_by (FK users).
- **História de Usuário**: Como Professor, quero abrir um ciclo de autoavaliação ao final de cada módulo prático, para que os alunos reflitam sobre seu domínio das habilidades.
- **Critérios de Aceitação**:
- Formulário vinculado a um módulo de aprendizagem e turma.
- Constraint validando opens_at < closes_at.
- Índice por (class_id, is_active) para exibir formulários abertos no portal do aluno.
- **Definição de Pronto (DoD)**: Tabela self_assessment_forms migrada e validada.
- **Observações Técnicas**: Base para BE-035 (criação de questionário) e FE-041 (interface de autoavaliação).

---

### [DB-032] Implementar Tabela de Respostas de Autoavaliação do Aluno (student_self_assessments)
- **ID**: `DB-032`
- **Título**: Implementar Tabela de Respostas de Autoavaliação do Aluno (student_self_assessments)
- **Área**: Banco de Dados
- **Epic**: EPIC-07: Autoavaliação & Motor de Diagnóstico Explicável
- **Lote / Sprint**: Lote 4 (S4)
- **Sequência na Squad**: ⬅️ Anterior: `DB-031` | ➡️ Próximo: `DB-033`
- **Dependências Diretas**: `DB-015, DB-017, DB-031`
- **Prioridade**: P1 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Persistir a percepção de domínio (nível 1 a 5) declarada pelo próprio estudante para cada competência técnica do módulo.
- **Descrição**: Criar tabela student_self_assessments com: id (UUID), form_id (FK self_assessment_forms), student_id (FK users), competency_id (FK competencies), perceived_level (INTEGER 1-5), confidence_score (INTEGER 1-5), difficulty_notes (TEXT opcional) e submitted_at (TIMESTAMP).
- **História de Usuário**: Como Estudante, quero registrar meu nível percebido em cada habilidade prática e apontar onde senti dificuldade na oficina.
- **Critérios de Aceitação**:
- Constraint UNIQUE em (form_id, student_id, competency_id).
- CHECK constraint garantindo perceived_level e confidence_score entre 1 e 5.
- Isolamento de acesso: um aluno jamais pode ler a autoavaliação de outro colega.
- **Definição de Pronto (DoD)**: Tabela migrada com restrições de integridade e unicidade.
- **Observações Técnicas**: Consumida pelo endpoint BE-036 e comparada com evidências reais em DB-038.

---

### [DB-033] Criar Tabela de Evidências Práticas de Habilidades (skill_evidences)
- **ID**: `DB-033`
- **Título**: Criar Tabela de Evidências Práticas de Habilidades (skill_evidences)
- **Área**: Banco de Dados
- **Epic**: EPIC-07: Autoavaliação & Motor de Diagnóstico Explicável
- **Lote / Sprint**: Lote 4 (S4)
- **Sequência na Squad**: ⬅️ Anterior: `DB-032` | ➡️ Próximo: `DB-034`
- **Dependências Diretas**: `DB-015, DB-026, DB-028`
- **Prioridade**: P1 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Consolidar as evidências acadêmicas reais (avaliações de bancada, rubricas e microavaliações) que comprovam o nível técnico do estudante em cada competência.
- **Descrição**: Criar tabela skill_evidences com: id (UUID), student_id (FK users), competency_id (FK competencies), source_submission_id (FK task_submissions opcional), source_assessment_id (FK academic_assessments opcional), verified_level (DECIMAL 3,2 de 1.00 a 5.00), verified_by (FK users role TEACHER) e recorded_at.
- **História de Usuário**: Como Sistema de Diagnóstico, quero reunir as evidências práticas avaliadas pelo professor por competência, para contrastar com a autoavaliação do estudante.
- **Critérios de Aceitação**:
- Vincula cada competência avaliada à sua evidência de origem (tarefa prática ou avaliação).
- Nível verificado pelo docente parametrizado na mesma escala (1 a 5) da autoavaliação.
- Índice composto em (student_id, competency_id).
- **Definição de Pronto (DoD)**: Tabela skill_evidences implementada e integrada ao fluxo de avaliação.
- **Observações Técnicas**: Garante que diagnósticos nunca tratem autoavaliação como prova definitiva sem evidência docente.

---

### [DB-034] Implementar Tabela de Alertas e Indicadores de Risco (academic_alerts)
- **ID**: `DB-034`
- **Título**: Implementar Tabela de Alertas e Indicadores de Risco (academic_alerts)
- **Área**: Banco de Dados
- **Epic**: EPIC-05: Dashboard Híbrido do Professor & Visão 360°
- **Lote / Sprint**: Lote 4 (S4)
- **Sequência na Squad**: ⬅️ Anterior: `DB-033` | ➡️ Próximo: `DB-035`
- **Dependências Diretas**: `DB-005, DB-017, DB-022, DB-025, DB-028`
- **Prioridade**: P0 | **Estimativa**: 5 SP | **Tipo**: feature
- **Objetivo**: Armazenar alertas precoces e explicáveis gerados para alunos que apresentam risco de queda de rendimento, faltas ou atraso em oficinas.
- **Descrição**: Criar tabela academic_alerts com: id (UUID), student_id (FK users), enrollment_id (FK enrollments), class_id (FK classes), module_id (FK learning_modules opcional), risk_level (enum RiskLevel: LOW, MODERATE, HIGH, CRITICAL), alert_category (enum: ATTENDANCE, GRADE_DROP, PENDING_TASKS, SELF_EVAL_GAP), explainable_reason (TEXT detalhando os dados e regra disparada), metric_snapshot (JSONB), status (enum: ACTIVE, ACKNOWLEDGED, RESOLVED), resolved_by (FK users opcional), resolution_notes (TEXT) e created_at.
- **História de Usuário**: Como Professor ou Coordenador, quero receber alertas fundamentados em evidências claras (ex: '3 tarefas práticas atrasadas e 74% de presença'), para agir preventivamente.
- **Critérios de Aceitação**:
- Campo explainable_reason obrigatório descrevendo de forma transparente o critério que gerou o alerta.
- metric_snapshot em JSONB guardando os indicadores exatos do momento da geração.
- Índices em (class_id, status, risk_level) para ordenação de prioridade no dashboard.
- **Definição de Pronto (DoD)**: Tabela academic_alerts migrada e pronta para o motor de regras (BE-032).
- **Observações Técnicas**: Alertas são indicadores pedagógicos de apoio ao docente, nunca rótulos permanentes ao estudante.

---

### [DB-035] Implementar Tabela de Diagnósticos Explicáveis de Turma (explainable_diagnostics)
- **ID**: `DB-035`
- **Título**: Implementar Tabela de Diagnósticos Explicáveis de Turma (explainable_diagnostics)
- **Área**: Banco de Dados
- **Epic**: EPIC-07: Autoavaliação & Motor de Diagnóstico Explicável
- **Lote / Sprint**: Lote 4 (S4)
- **Sequência na Squad**: ⬅️ Anterior: `DB-034` | ➡️ Próximo: `DB-036`
- **Dependências Diretas**: `DB-032, DB-033, DB-034`
- **Prioridade**: P1 | **Estimativa**: 5 SP | **Tipo**: feature
- **Objetivo**: Persistir relatórios de diagnóstico pedagógico comparando autoavaliações, notas práticas e frequência com total rastreabilidade dos critérios utilizados.
- **Descrição**: Criar tabela explainable_diagnostics com: id (UUID), student_id (FK users), class_id (FK classes), module_id (FK learning_modules), competency_id (FK competencies opcional), self_perceived_level (DECIMAL 3,2), teacher_verified_level (DECIMAL 3,2), discrepancy_gap (DECIMAL 3,2), diagnostic_type (enum: ALIGNED, OVERCONFIDENCE_RISK, UNDERCONFIDENCE_SUPPORT, INSUFFICIENT_EVIDENCE), explanation_text (TEXT), limitations_note (TEXT), recommended_action (TEXT) e generated_at.
- **História de Usuário**: Como Professor, quero que o sistema destaque divergências entre o que o aluno acha que sabe e o que ele demonstrou na oficina, explicando critérios e limitações.
- **Critérios de Aceitação**:
- Registra explicitamente explanation_text e limitations_note (ex: 'Baseado em 2 entregas práticas; autoavaliação isolada não comprova domínio').
- Calcula discrepancy_gap (diferença entre nível percebido e nível avaliado).
- Índice em (class_id, diagnostic_type).
- **Definição de Pronto (DoD)**: Tabela explainable_diagnostics migrada e testada com casos de divergência.
- **Observações Técnicas**: Alimenta diretamente BE-037, BE-038 e o componente comparativo FE-042.

---

### [DB-036] Criar View Analítica Consolidada de Desempenho do Aluno (vw_student_360_performance)
- **ID**: `DB-036`
- **Título**: Criar View Analítica Consolidada de Desempenho do Aluno (vw_student_360_performance)
- **Área**: Banco de Dados
- **Epic**: EPIC-05: Dashboard Híbrido do Professor & Visão 360°
- **Lote / Sprint**: Lote 4 (S4)
- **Sequência na Squad**: ⬅️ Anterior: `DB-035` | ➡️ Próximo: `DB-037`
- **Dependências Diretas**: `DB-017, DB-022, DB-025, DB-028, DB-034`
- **Prioridade**: P0 | **Estimativa**: 5 SP | **Tipo**: feature
- **Objetivo**: Otimizar a consulta da ficha 360° do estudante e do dashboard híbrido do professor por meio de uma View SQL pré-agregada.
- **Descrição**: Criar view SQL vw_student_360_performance consolidando por matrícula (enrollment_id): dados do aluno, turma, média geral ponderada, percentual de presença atualizado, total de atividades práticas concluídas, pendentes e atrasadas, quantidade de alertas ativos e nível de risco atual.
- **História de Usuário**: Como Desenvolvedor Back-end, quero consultar uma view única de alta performance para montar o Dashboard do Professor e a Ficha 360° sem dezenas de joins lentos.
- **Critérios de Aceitação**:
- View criada via migration SQL do Prisma.
- Calcula corretamente contadores de tarefas PENDING, SUBMITTED, EVALUATED e LATE.
- Tempo de execução inferior a 30ms para turmas de até 50 alunos.
- **Definição de Pronto (DoD)**: View vw_student_360_performance ativa no PostgreSQL e testada com EXPLAIN ANALYZE.
- **Observações Técnicas**: Consumida diretamente pelos endpoints BE-031, BE-034 e telas FE-031, FE-034 e FE-035.

---

### [DB-037] Criar View Analítica de Frequência e Evasão por Módulo (vw_module_attendance_risk)
- **ID**: `DB-037`
- **Título**: Criar View Analítica de Frequência e Evasão por Módulo (vw_module_attendance_risk)
- **Área**: Banco de Dados
- **Epic**: EPIC-05: Dashboard Híbrido do Professor & Visão 360°
- **Lote / Sprint**: Lote 4 (S4)
- **Sequência na Squad**: ⬅️ Anterior: `DB-036` | ➡️ Próximo: `DB-038`
- **Dependências Diretas**: `DB-014, DB-021, DB-022`
- **Prioridade**: P1 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Prover indicadores agregados de presença por disciplina e módulo prático para identificar precocemente risco de reprovação por faltas (<75%).
- **Descrição**: Criar view SQL vw_module_attendance_risk calculando: total de horas ministradas no módulo, horas de presença do estudante, horas faltadas, percentual exato de frequência e flag booleana is_attendance_critical (quando frequência < 78%).
- **História de Usuário**: Como Coordenador e Professor, quero identificar rapidamente alunos que estão se aproximando do limite de 25% de faltas antes que reprovem.
- **Critérios de Aceitação**:
- Trata divisão por zero quando nenhuma aula foi ministrada ainda (retorna 100%).
- Considera faltas justificadas (JUSTIFIED) separadamente de faltas não justificadas.
- Integrada com o motor de alertas (BE-032).
- **Definição de Pronto (DoD)**: View criada em migration SQL e validada contra registros do seed.
- **Observações Técnicas**: Suporta o indicador visual de presença 75% no frontend (FE-023).

---

### [DB-038] Criar View de Discrepância: Autoavaliação vs Avaliação do Professor (vw_self_eval_discrepancy)
- **ID**: `DB-038`
- **Título**: Criar View de Discrepância: Autoavaliação vs Avaliação do Professor (vw_self_eval_discrepancy)
- **Área**: Banco de Dados
- **Epic**: EPIC-07: Autoavaliação & Motor de Diagnóstico Explicável
- **Lote / Sprint**: Lote 4 (S4)
- **Sequência na Squad**: ⬅️ Anterior: `DB-037` | ➡️ Próximo: `DB-039`
- **Dependências Diretas**: `DB-032, DB-033, DB-035`
- **Prioridade**: P1 | **Estimativa**: 5 SP | **Tipo**: feature
- **Objetivo**: Cruzar automaticamente no banco as notas de autoavaliação do aluno com a média das evidências práticas avaliadas pelo professor por competência.
- **Descrição**: Criar view SQL vw_self_eval_discrepancy relacionando student_self_assessments e skill_evidences por (student_id, competency_id), calculando o delta (perceived_level - avg_verified_level) e classificando divergências >= 1.5 pontos para revisão pedagógica.
- **História de Usuário**: Como Professor, quero visualizar instantaneamente onde a percepção do aluno diverge da avaliação prática de bancada.
- **Critérios de Aceitação**:
- Retorna lado a lado: nível autoavaliado, nível verificado pelo professor, quantidade de evidências e delta.
- Destaca casos de superestimação (risco técnico/segurança) e subestimação (insegurança do aluno).
- Consulta otimizada para os gráficos radar e comparativo (FE-038 e FE-042).
- **Definição de Pronto (DoD)**: View SQL funcional e validada pelo serviço de diagnóstico (BE-037 / BE-038).
- **Observações Técnicas**: Chave para entregar a inteligência explicável do projeto sem depender de caixa-preta.

---

### [DB-039] Implementar Tabela de Histórico e Linha do Tempo Acadêmica (student_milestone_history)
- **ID**: `DB-039`
- **Título**: Implementar Tabela de Histórico e Linha do Tempo Acadêmica (student_milestone_history)
- **Área**: Banco de Dados
- **Epic**: EPIC-06: Portal de Autonomia do Aluno & Pendências
- **Lote / Sprint**: Lote 4 (S4)
- **Sequência na Squad**: ⬅️ Anterior: `DB-038` | ➡️ Próximo: `DB-040`
- **Dependências Diretas**: `DB-014, DB-017, DB-025`
- **Prioridade**: P2 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Registrar a linha do tempo de evolução do estudante ao longo dos módulos (módulos concluídos, evolução de nível de habilidade e marcos atingidos).
- **Descrição**: Criar tabela student_milestone_history com: id (UUID), student_id (FK users), enrollment_id (FK enrollments), module_id (FK learning_modules opcional), milestone_type (enum: MODULE_COMPLETED, SKILL_LEVEL_UP, PERFECT_ATTENDANCE, RECOVERY_ACHIEVED), title (VARCHAR 150), description (TEXT), metadata (JSONB) e achieved_at (TIMESTAMP).
- **História de Usuário**: Como Estudante, quero visualizar minha trajetória de evolução desde o início do curso técnico, percebendo meu progresso real.
- **Critérios de Aceitação**:
- Eventos ordenados cronologicamente por achieved_at.
- Vinculação íntegra com matrícula e módulo prático.
- Índice composto em (student_id, achieved_at DESC).
- **Definição de Pronto (DoD)**: Tabela migrada e alimentando a rota do Portal do Aluno (BE-034 / FE-039).
- **Observações Técnicas**: Reforça o engajamento positivo e a autonomia do estudante.

---

### [DB-040] Criar Seed de Diagnósticos e Alertas Simulados para Validação de Dashboards
- **ID**: `DB-040`
- **Título**: Criar Seed de Diagnósticos e Alertas Simulados para Validação de Dashboards
- **Área**: Banco de Dados
- **Epic**: EPIC-05: Dashboard Híbrido do Professor & Visão 360°
- **Lote / Sprint**: Lote 4 (S4)
- **Sequência na Squad**: ⬅️ Anterior: `DB-039` | ➡️ Próximo: `DB-041`
- **Dependências Diretas**: `DB-030, DB-031, DB-032, DB-033, DB-034, DB-035, DB-039`
- **Prioridade**: P1 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Popular formulários de autoavaliação, evidências de habilidades, diagnósticos explicáveis e alertas de risco no seed para homologação das telas do Lote 4.
- **Descrição**: Atualizar prisma/seed.ts inserindo respostas de autoavaliação, registros em skill_evidences, 8 alertas acadêmicos explicáveis (LOW, MODERATE, HIGH, CRITICAL) e 10 diagnósticos comparativos entre autoavaliação e avaliação docente.
- **História de Usuário**: Como Equipe do Projeto, queremos demonstrar os dashboards do professor e do aluno repletos de indicadores e diagnósticos explicáveis na apresentação.
- **Critérios de Aceitação**:
- Todos os gráficos e cards dos Lotes 4 e 5 renderizam dados coerentes após rodar npm run db:seed.
- Inclui exemplos reais de divergência em Metrologia e Tornearia.
- Idempotente e livre de erros de chave duplicada.
- **Definição de Pronto (DoD)**: Seed completo do Lote 4 rodando em menos de 5 segundos.
- **Observações Técnicas**: Sincronizado com os contratos esperados em BE-031 a BE-039 e FE-031 a FE-042.

---

### [DB-041] Implementar Tabela de Mural de Avisos da Turma (class_announcements)
- **ID**: `DB-041`
- **Título**: Implementar Tabela de Mural de Avisos da Turma (class_announcements)
- **Área**: Banco de Dados
- **Epic**: EPIC-08: Comunicação Oficial & Solicitações Confidenciais
- **Lote / Sprint**: Lote 5 (S5)
- **Sequência na Squad**: ⬅️ Anterior: `DB-040` | ➡️ Próximo: `DB-042`
- **Dependências Diretas**: `DB-006, DB-012, DB-013`
- **Prioridade**: P1 | **Estimativa**: 2 SP | **Tipo**: feature
- **Objetivo**: Armazenar comunicados oficiais enviados por professores e coordenadores direcionados a uma turma ou disciplina.
- **Descrição**: Criar tabela class_announcements com: id (UUID), class_id (FK classes), subject_id (FK subjects opcional), author_id (FK users), title (VARCHAR 150), content (TEXT), priority (enum: NORMAL, IMPORTANT, URGENT), is_pinned (BOOLEAN padrão false), published_at (TIMESTAMP) e expires_at (TIMESTAMP opcional).
- **História de Usuário**: Como Professor ou Coordenador, quero publicar avisos oficiais no mural da turma (ex: mudança de laboratório ou uso obrigatório de óculos de proteção).
- **Critérios de Aceitação**:
- Avisos vinculados obrigatoriamente a uma turma válida.
- Suporte a fixação no topo (is_pinned = true) e prioridade visual.
- Índice composto em (class_id, is_pinned DESC, published_at DESC).
- **Definição de Pronto (DoD)**: Tabela class_announcements migrada e testada.
- **Observações Técnicas**: Alimenta diretamente BE-041, BE-042 e a tela de mural FE-043.

---

### [DB-042] Implementar Tabela de Solicitações de Apoio e Mentoria Confidenciais (help_requests)
- **ID**: `DB-042`
- **Título**: Implementar Tabela de Solicitações de Apoio e Mentoria Confidenciais (help_requests)
- **Área**: Banco de Dados
- **Epic**: EPIC-08: Comunicação Oficial & Solicitações Confidenciais
- **Lote / Sprint**: Lote 5 (S5)
- **Sequência na Squad**: ⬅️ Anterior: `DB-041` | ➡️ Próximo: `DB-043`
- **Dependências Diretas**: `DB-005, DB-013, DB-014, DB-017`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Persistir os pedidos de ajuda e mentoria feitos pelos alunos com proteção estrita de confidencialidade perante outros estudantes.
- **Descrição**: Criar tabela help_requests com: id (UUID), student_id (FK users), enrollment_id (FK enrollments), subject_id (FK subjects), module_id (FK learning_modules opcional), assigned_teacher_id (FK users opcional), category (enum: TECHNICAL_DOUBT, PRACTICAL_DIFFICULTY, PERSONAL_PEDAGOGICAL), subject_title (VARCHAR 150), description (TEXT), is_confidential (BOOLEAN padrão true), status (enum HelpRequestStatus: OPEN, IN_PROGRESS, RESOLVED, CLOSED), resolution_summary (TEXT), created_at, updated_at e closed_at.
- **História de Usuário**: Como Estudante, quero solicitar ajuda pedagógica de forma confidencial quando tiver dificuldade em uma máquina ou matéria, sem me expor para a turma.
- **Critérios de Aceitação**:
- Flag is_confidential ativa por padrão garantindo que nenhum outro estudante veja a solicitação.
- Rastreamento completo de estados: OPEN -> IN_PROGRESS -> RESOLVED -> CLOSED.
- Índices em (assigned_teacher_id, status) e (student_id, status).
- **Definição de Pronto (DoD)**: Tabela help_requests migrada e validada com regras de sigilo.
- **Observações Técnicas**: Suporta os endpoints BE-043, BE-044 e as telas FE-044 (aluno) e FE-045 (professor).

---

### [DB-043] Implementar Tabela de Observações Pedagógicas Restritas (pedagogical_notes)
- **ID**: `DB-043`
- **Título**: Implementar Tabela de Observações Pedagógicas Restritas (pedagogical_notes)
- **Área**: Banco de Dados
- **Epic**: EPIC-08: Comunicação Oficial & Solicitações Confidenciais
- **Lote / Sprint**: Lote 5 (S5)
- **Sequência na Squad**: ⬅️ Anterior: `DB-042` | ➡️ Próximo: `DB-044`
- **Dependências Diretas**: `DB-006, DB-009, DB-017`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Armazenar anotações pedagógicas de acompanhamento registradas por professores e coordenação com controle de acesso rigoroso.
- **Descrição**: Criar tabela pedagogical_notes com: id (UUID), student_id (FK users), enrollment_id (FK enrollments), author_id (FK users role TEACHER ou COORDINATOR), visibility_scope (enum: PRIVATE_AUTHOR, TEACHERS_AND_COORD, COORDINATION_ONLY), category (enum: INTERVENTION, MENTORING, BEHAVIORAL, ACCOMMODATION), note_content (TEXT), requires_followup (BOOLEAN), followup_date (DATE opcional), created_at e updated_at.
- **História de Usuário**: Como Professor ou Coordenador, quero registrar observações pedagógicas restritas sobre intervenções realizadas, sem jamais expor esses registros a usuários não autorizados.
- **Critérios de Aceitação**:
- Coluna visibility_scope restringindo quem pode ler a observação no backend.
- Vínculo estrito com aluno matriculado (enrollments).
- Toda leitura ou escrita em pedagogical_notes deve gerar rastro em audit_logs.
- **Definição de Pronto (DoD)**: Tabela pedagogical_notes criada com constraints de escopo de visibilidade.
- **Observações Técnicas**: Integrada com BE-045 (endpoint protegido) e FE-046 (modal de observações restritas).

---

### [DB-044] Implementar Tabela de Conversações e Mensagens Internas (chat_messages)
- **ID**: `DB-044`
- **Título**: Implementar Tabela de Conversações e Mensagens Internas (chat_messages)
- **Área**: Banco de Dados
- **Epic**: EPIC-08: Comunicação Oficial & Solicitações Confidenciais
- **Lote / Sprint**: Lote 5 (S5)
- **Sequência na Squad**: ⬅️ Anterior: `DB-043` | ➡️ Próximo: `DB-045`
- **Dependências Diretas**: `DB-006, DB-042`
- **Prioridade**: P2 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Permitir troca de mensagens contextualizadas dentro de uma solicitação de ajuda ou acompanhamento pedagógico entre aluno e professor.
- **Descrição**: Criar tabela chat_messages com: id (UUID), help_request_id (FK help_requests com cascade), sender_id (FK users), message_body (TEXT), is_read (BOOLEAN padrão false), read_at (TIMESTAMP opcional) e sent_at (TIMESTAMP).
- **História de Usuário**: Como Aluno e Professor, queremos conversar dentro do chamado de ajuda com confirmação de leitura, para alinhar horários de monitoria ou tirar dúvidas.
- **Critérios de Aceitação**:
- Mensagens vinculadas a um help_request_id existente.
- Controle de estado de leitura (is_read e read_at).
- Índice composto em (help_request_id, sent_at ASC).
- **Definição de Pronto (DoD)**: Tabela chat_messages migrada e integrada ao fluxo de atendimento de ajuda.
- **Observações Técnicas**: Apenas o estudante titular da solicitação e os docentes autorizados podem consultar as mensagens.

---

### [DB-045] Implementar Tabela de Conquistas e Níveis de Gamificação (gamification_badges)
- **ID**: `DB-045`
- **Título**: Implementar Tabela de Conquistas e Níveis de Gamificação (gamification_badges)
- **Área**: Banco de Dados
- **Epic**: EPIC-09: Gamificação Pedagógica Transparente & Níveis
- **Lote / Sprint**: Lote 5 (S5)
- **Sequência na Squad**: ⬅️ Anterior: `DB-044` | ➡️ Próximo: `DB-046`
- **Dependências Diretas**: `DB-015`
- **Prioridade**: P2 | **Estimativa**: 2 SP | **Tipo**: feature
- **Objetivo**: Cadastrar insígnias (badges) e regras transparentes de pontuação baseadas no domínio de competências e assiduidade.
- **Descrição**: Criar tabela gamification_badges com: id (UUID), code (UNIQUE, ex: 'BADGE-METROLOGIA-100'), title (ex: 'Mestre do Micrômetro'), description (TEXT), criteria_explanation (TEXT transparente explicando como conquistar), icon_name (VARCHAR 80), xp_reward (INTEGER), competency_id (FK competencies opcional) e is_active (BOOLEAN).
- **História de Usuário**: Como Estudante, quero conhecer claramente os critérios para desbloquear conquistas e subir de nível de habilidade nas oficinas.
- **Critérios de Aceitação**:
- Campo criteria_explanation obrigatório garantindo transparência na regra de pontuação.
- Código único para cada conquista.
- XP positivo e parametrizado sem gerar ranking punitivo.
- **Definição de Pronto (DoD)**: Tabela gamification_badges migrada e populada com conquistas técnicas SENAI.
- **Observações Técnicas**: Base para o motor de gamificação (BE-046, BE-047) e tela de conquistas (FE-047).

---

### [DB-046] Criar Tabela de Conquistas Desbloqueadas pelos Estudantes (student_achievements)
- **ID**: `DB-046`
- **Título**: Criar Tabela de Conquistas Desbloqueadas pelos Estudantes (student_achievements)
- **Área**: Banco de Dados
- **Epic**: EPIC-09: Gamificação Pedagógica Transparente & Níveis
- **Lote / Sprint**: Lote 5 (S5)
- **Sequência na Squad**: ⬅️ Anterior: `DB-045` | ➡️ Próximo: `DB-047`
- **Dependências Diretas**: `DB-017, DB-045`
- **Prioridade**: P2 | **Estimativa**: 2 SP | **Tipo**: feature
- **Objetivo**: Registrar as insígnias conquistadas por cada estudante e sua pontuação acumulada de experiência técnica.
- **Descrição**: Criar tabela student_achievements com: id (UUID), student_id (FK users), enrollment_id (FK enrollments), badge_id (FK gamification_badges), unlocked_at (TIMESTAMP), origin_reference (VARCHAR 150 indicando qual módulo ou entrega concedeu a conquista).
- **História de Usuário**: Como Estudante, quero ver minhas conquistas salvas no meu portal sempre que concluir um módulo prático com excelência.
- **Critérios de Aceitação**:
- Constraint UNIQUE em (student_id, badge_id) impedindo ganho duplicado da mesma insígnia.
- FK íntegra com gamification_badges e enrollments.
- Índice por (student_id, unlocked_at DESC).
- **Definição de Pronto (DoD)**: Tabela student_achievements migrada e testada.
- **Observações Técnicas**: Conecta-se com BE-046, BE-047 e FE-047.

---

### [DB-047] Otimizar Esquema com Índices B-Tree e Compostos para Consultas Frequentes
- **ID**: `DB-047`
- **Título**: Otimizar Esquema com Índices B-Tree e Compostos para Consultas Frequentes
- **Área**: Banco de Dados
- **Epic**: EPIC-10: Relatórios, Governança de Dados & Qualidade
- **Lote / Sprint**: Lote 5 (S5)
- **Sequência na Squad**: ⬅️ Anterior: `DB-046` | ➡️ Próximo: `DB-048`
- **Dependências Diretas**: `DB-022, DB-025, DB-028, DB-034, DB-042`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: melhoria
- **Objetivo**: Garantir alta performance (<50ms) nas queries de dashboards, filtros, paginação e relatórios com criação estratégica de índices.
- **Descrição**: Analisar planos de execução (EXPLAIN ANALYZE) de todas as consultas dos Lotes 1 a 5 e adicionar índices compostos no Prisma e SQL: (class_id, status) em enrollments, (student_id, status) em task_submissions, (class_id, risk_level) em academic_alerts e índices parciais para registros ativos.
- **História de Usuário**: Como Engenheiro de Software, quero que os dashboards e filtros carreguem instantaneamente mesmo com milhares de registros de frequência e notas.
- **Critérios de Aceitação**:
- Nenhum Sequential Scan em tabelas críticas durante consultas filtradas por turma ou aluno.
- Migration de índices documentada e aplicada.
- Relatório de ganho de performance com EXPLAIN ANALYZE antes e depois.
- **Definição de Pronto (DoD)**: Índices aplicados e validados nos testes de carga (BE-040).
- **Observações Técnicas**: Suporta diretamente os relatórios e exportações (BE-049 / FE-048).

---

### [DB-048] Implementar Rotina de Backup Automatizado e Script de Restauração (pg_dump/restore)
- **ID**: `DB-048`
- **Título**: Implementar Rotina de Backup Automatizado e Script de Restauração (pg_dump/restore)
- **Área**: Banco de Dados
- **Epic**: EPIC-10: Relatórios, Governança de Dados & Qualidade
- **Lote / Sprint**: Lote 5 (S5)
- **Sequência na Squad**: ⬅️ Anterior: `DB-047` | ➡️ Próximo: `DB-049`
- **Dependências Diretas**: `DB-003, DB-029, DB-036`
- **Prioridade**: P1 | **Estimativa**: 3 SP | **Tipo**: infraestrutura
- **Objetivo**: Proteger o banco de dados contra perda acidental com scripts automatizados de backup comprimido e restauração validada.
- **Descrição**: Criar scripts em scripts/db-backup.sh (e equivalente PowerShell/Node scripts/db-backup.js) executando pg_dump em formato custom comprimido (-Fc) com timestamp, rotação dos últimos 7 backups e script de restore com verificação de integridade pós-restauração.
- **História de Usuário**: Como Administrador de Infraestrutura, quero realizar backup e restore confiáveis do banco acadêmico em poucos segundos.
- **Critérios de Aceitação**:
- Script gera arquivo de dump datado na pasta backups/ (ignorada pelo git).
- Script de restauração recupera 100% do schema, views, triggers e dados em banco limpo.
- Procedimento documentado em DOC-017.
- **Definição de Pronto (DoD)**: Teste completo de backup seguido de restore executado com sucesso.
- **Observações Técnicas**: Requisito essencial de segurança e continuidade de negócios.

---

### [DB-049] Implementar Políticas de Retenção de Dados e Anonimização LGPD
- **ID**: `DB-049`
- **Título**: Implementar Políticas de Retenção de Dados e Anonimização LGPD
- **Área**: Banco de Dados
- **Epic**: EPIC-10: Relatórios, Governança de Dados & Qualidade
- **Lote / Sprint**: Lote 5 (S5)
- **Sequência na Squad**: ⬅️ Anterior: `DB-048` | ➡️ Próximo: `DB-050`
- **Dependências Diretas**: `DB-006, DB-007, DB-009, DB-042, DB-043`
- **Prioridade**: P1 | **Estimativa**: 5 SP | **Tipo**: feature
- **Objetivo**: Atender às exigências da LGPD implementando rotina de anonimização de dados pessoais de ex-alunos após o período legal de retenção sem quebrar estatísticas.
- **Descrição**: Criar procedure/script de anonimização LGPD que substitui nome, e-mail, telefone e textos livres confidenciais por hashes irreversíveis para contas inativas/expiradas ou mediante solicitação formal, preservando apenas os agregados estatísticos anônimos de desempenho por curso/módulo.
- **História de Usuário**: Como Encarregado de Proteção de Dados (DPO), quero garantir minimização, retenção controlada e anonimização segura dos dados pessoais dos estudantes.
- **Critérios de Aceitação**:
- Função de anonimização remove PII (Personally Identifiable Information) em users, user_profiles, help_requests e pedagogical_notes.
- Mantém integridade referencial das métricas históricas anônimas da turma.
- Registra execução no audit_logs.
- **Definição de Pronto (DoD)**: Rotina de anonimização testada e documentada no relatório LGPD (DOC-017).
- **Observações Técnicas**: Cumpre integralmente a seção 14 (Segurança, privacidade e LGPD).

---

### [DB-050] Gerar Dicionário de Dados Automatizado e Validação Final de Integridade
- **ID**: `DB-050`
- **Título**: Gerar Dicionário de Dados Automatizado e Validação Final de Integridade
- **Área**: Banco de Dados
- **Epic**: EPIC-10: Relatórios, Governança de Dados & Qualidade
- **Lote / Sprint**: Lote 5 (S5)
- **Sequência na Squad**: ⬅️ Anterior: `DB-049` | ➡️ Próximo: `Marco Final Concluído (100%)`
- **Dependências Diretas**: `DB-001, DB-010, DB-020, DB-030, DB-040, DB-047, DB-048, DB-049`
- **Prioridade**: P0 | **Estimativa**: 2 SP | **Tipo**: teste
- **Objetivo**: Executar a suíte final de testes de integridade referencial de todas as 50 tarefas de banco de dados e exportar o schema consolidado para fechamento do projeto.
- **Descrição**: Criar suíte de testes de banco (prisma/verify-schema-integrity.ts) que valida todas as tabelas, enums, views (vw_student_360_performance, vw_module_attendance_risk, vw_self_eval_discrepancy), triggers, constraints CHECK/FOREIGN KEY e gera relatório final sincronizado com DOC-008, DOC-009 e DOC-020.
- **História de Usuário**: Como Tech Lead de Banco de Dados, quero validar que 100% da camada de dados está íntegra, populada e sincronizada com o Back-end (BE-050) e Front-end (FE-050).
- **Critérios de Aceitação**:
- Script valida que nenhuma nota, frequência, autoavaliação ou observação pode ser inserida para aluno ou turma inexistente.
- Confirma funcionamento de todas as migrations e seeds do Lote 1 ao Lote 5.
- Exporta resumo atualizado para o Dicionário de Dados (DOC-009) e Relatório Final (DOC-020).
- **Definição de Pronto (DoD)**: Camada de Banco de Dados 100% concluída, testada e homologada junto a BE-050, FE-050 e DOC-020.
- **Observações Técnicas**: Marco de encerramento (Card 50/50) da squad de Banco de Dados.

