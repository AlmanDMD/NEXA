# 🎨 Backlog de Front-end (Interface & Experiência do Usuário) — Projeto NEXA
## 50 Cards Exclusivos de Interface React (`FE-001` a `FE-050`)

Este documento especifica os 50 cards da camada de interface do usuário do **Sistema Inteligente de Monitoramento do Desempenho Acadêmico — SENAI**.
Construído com **React 19 + TypeScript + Vite + Tailwind CSS v4**, com design system consistente, acessibilidade (WCAG 2.1 AA), estados visuais completos (carregamento, vazio, erro) e tipagem desacoplada permitindo desenvolvimento em lotes modulares de 10 cards.

---

### Resumo dos Lotes de Implementação
- **Lote 1 (FE-001 a FE-010)**: Design System Base, Variáveis Tailwind v4, Componentes Primitivos (Botões, Modais, Inputs), Layout Global Responsivo e Sidebar.
- **Lote 2 (FE-011 a FE-020)**: Fluxos de Autenticação, Proteção de Rotas, Gestão de Usuários, Turmas, Disciplinas e Módulos SENAI.
- **Lote 3 (FE-021 a FE-030)**: Diário de Classe Digital, Interface de Chamada Rápida em 1 Clique, Registro de Atividades Práticas de Oficina e Notas.
- **Lote 4 (FE-031 a FE-040)**: Dashboard Híbrido do Professor com Alertas Explicáveis de Risco, Portal de Autonomia do Aluno e Painel de Pendências.
- **Lote 5 (FE-041 a FE-050)**: Tela de Autoavaliação de Habilidades, Radar de Competências, Canal de Pedidos de Ajuda Confidenciais, Mural e Testes E2E.

---

### Tabela Resumo dos 50 Cards de Front-end

| ID | Título | Componente / Rota | Epic | Prioridade | Estimativa | Lote |
|---|---|---|---|---|---|---|
| `FE-001` | Configurar Design System Base e Tokens de Cores SENAI no Tailwind v4 | Global | EPIC-01 | P0 | 3 SP | Lote 1 |
| `FE-002` | Criar Biblioteca de Componentes Primitivos: Botões, Badges e Tags | `src/components/ui` | EPIC-01 | P0 | 3 SP | Lote 1 |
| `FE-003` | Criar Componentes de Formulário com Validação Visual e Acessibilidade | `src/components/forms` | EPIC-01 | P0 | 3 SP | Lote 1 |
| `FE-004` | Criar Componente de Modal, Dialog e Confirmação com Foco Acessível | `src/components/ui/Modal` | EPIC-01 | P0 | 2 SP | Lote 1 |
| `FE-005` | Criar Componentes de Tabela de Dados com Paginação, Ordenação e Busca | `src/components/tables` | EPIC-01 | P0 | 5 SP | Lote 1 |
| `FE-006` | Implementar Estados Visuais Padrão: Skeleton Loading, Erro e Vazio (Empty State) | `src/components/feedback` | EPIC-01 | P0 | 3 SP | Lote 1 |
| `FE-007` | Desenvolver Layout Principal (Header com Notificações e Perfil do Usuário) | `src/layouts/AppHeader` | EPIC-01 | P0 | 3 SP | Lote 1 |
| `FE-008` | Desenvolver Sidebar Retrátil com Navegação Dinâmica Baseada em Papéis (RBAC) | `src/layouts/Sidebar` | EPIC-01 | P0 | 3 SP | Lote 1 |
| `FE-009` | Configurar React Router DOM com Rotas Públicas, Privadas e Guardas de Acesso | `src/routes` | EPIC-01 | P0 | 3 SP | Lote 1 |
| `FE-010` | Criar Cliente HTTP Axios/Fetch Centralizado com Tratamento de Sessão e Toasts | `src/services/api` | EPIC-01 | P0 | 3 SP | Lote 1 |
| `FE-011` | Desenvolver Tela de Login Responsiva com Feedback de Validação | `/login` | EPIC-01 | P0 | 3 SP | Lote 2 |
| `FE-012` | Implementar Contexto Global de Autenticação (`AuthContext`) com Persistência | `src/contexts/Auth` | EPIC-01 | P0 | 3 SP | Lote 2 |
| `FE-013` | Criar Tela de Visualização e Edição de Perfil do Usuário | `/perfil` | EPIC-01 | P1 | 2 SP | Lote 2 |
| `FE-014` | Desenvolver Painel Administrativo de Listagem e Gestão de Usuários | `/admin/usuarios` | EPIC-01 | P0 | 5 SP | Lote 2 |
| `FE-015` | Criar Modal de Criação e Edição de Usuários com Definição de Papéis | `/admin/usuarios/novo` | EPIC-01 | P0 | 3 SP | Lote 2 |
| `FE-016` | Desenvolver Tela de Gerenciamento de Turmas e Períodos Letivos | `/turmas` | EPIC-02 | P0 | 5 SP | Lote 2 |
| `FE-017` | Criar Tela de Gerenciamento de Disciplinas e Matriz Curricular | `/disciplinas` | EPIC-02 | P0 | 3 SP | Lote 2 |
| `FE-018` | Desenvolver Interface de Módulos Práticos SENAI (Metrologia, Usinagem) | `/modulos` | EPIC-02 | P0 | 3 SP | Lote 2 |
| `FE-019` | Criar Tela de Gestão de Matrículas e Vínculo de Estudantes à Turma | `/turmas/:id/alunos` | EPIC-02 | P0 | 5 SP | Lote 2 |
| `FE-020` | Criar Tela de Associação de Professores às Turmas e Oficinas | `/atribuicoes` | EPIC-02 | P1 | 3 SP | Lote 2 |
| `FE-021` | Desenvolver Diário de Classe: Visão Geral de Aulas da Disciplina | `/aulas` | EPIC-03 | P0 | 3 SP | Lote 3 |
| `FE-022` | Criar Interface de Chamada Rápida de Frequência em 1 Clique (Matriz da Turma) | `/aulas/:id/chamada` | EPIC-03 | P0 | 5 SP | Lote 3 |
| `FE-023` | Implementar Indicador Visual de Presença/Faltas com Alerta de Limite 75% | `/alunos/:id/frequencia` | EPIC-03 | P0 | 3 SP | Lote 3 |
| `FE-024` | Criar Painel de Cadastro e Listagem de Atividades Práticas de Oficina | `/atividades-praticas` | EPIC-04 | P0 | 3 SP | Lote 3 |
| `FE-025` | Desenvolver Componente de Registro Rápido de Conclusão Prática pelo Docente | `/oficina/registro-rapido` | EPIC-04 | P0 | 5 SP | Lote 3 |
| `FE-026` | Criar Modal de Avaliação por Rubricas de Habilidade Técnica (Tolerâncias/Acabamento) | Componente Rubrica | EPIC-04 | P1 | 5 SP | Lote 3 |
| `FE-027` | Desenvolver Tela de Lançamento de Notas de Avaliações e Provas | `/avaliacoes/notas` | EPIC-03 | P0 | 5 SP | Lote 3 |
| `FE-028` | Criar Visualizador de Médias e Histórico Parcial por Aluno e Turma | `/turmas/:id/notas` | EPIC-03 | P0 | 3 SP | Lote 3 |
| `FE-029` | Implementar Filtros Avançados por Disciplina, Módulo e Período nas Tabelas | Componente Filtro | EPIC-03 | P1 | 2 SP | Lote 3 |
| `FE-030` | Testes Unitários de Componentes de Lançamento de Notas e Frequência | Testes Vitest | EPIC-03 | P0 | 3 SP | Lote 3 |
| `FE-031` | Desenvolver Dashboard do Professor: Visão Geral e Indicadores-Chave (KPIs) | `/professor/dashboard` | EPIC-05 | P0 | 5 SP | Lote 4 |
| `FE-032` | Criar Card de Aluno em Risco Acadêmico com Motivo Explicável e Ação Rápida | Componente Risco | EPIC-05 | P0 | 3 SP | Lote 4 |
| `FE-033` | Criar Gráfico de Evolução de Habilidades e Desempenho da Turma | Componente Gráfico | EPIC-05 | P1 | 5 SP | Lote 4 |
| `FE-034` | Desenvolver Visão 360° do Aluno (Ficha Completa: Notas, Faltas e Habilidades) | `/professor/alunos/:id` | EPIC-05 | P0 | 5 SP | Lote 4 |
| `FE-035` | Desenvolver Portal de Autonomia do Aluno (Visão Inicial do Estudante) | `/aluno/painel` | EPIC-06 | P0 | 5 SP | Lote 4 |
| `FE-036` | Criar Painel de Tarefas Pendentes, Concluídas e Atrasadas do Estudante | `/aluno/pendencias` | EPIC-06 | P0 | 3 SP | Lote 4 |
| `FE-037` | Desenvolver Visualização de Notas e Frequência do Próprio Aluno | `/aluno/desempenho` | EPIC-06 | P0 | 3 SP | Lote 4 |
| `FE-038` | Criar Gráfico Radar de Competências Técnicas do Aluno (Ex: Tornearia, Fresamento) | `/aluno/competencias` | EPIC-06 | P1 | 5 SP | Lote 4 |
| `FE-039` | Desenvolver Linha do Tempo de Conquistas e Marcos Acadêmicos | `/aluno/trajetoria` | EPIC-06 | P2 | 3 SP | Lote 4 |
| `FE-040` | Implementar Responsividade Mobile do Dashboard e Portal do Aluno | Global Mobile | EPIC-06 | P0 | 3 SP | Lote 4 |
| `FE-041` | Desenvolver Interface de Autoavaliação de Domínio de Habilidades Práticas | `/aluno/autoavaliacao` | EPIC-07 | P1 | 5 SP | Lote 5 |
| `FE-042` | Criar Componente Comparativo Visual: Autoavaliação vs Avaliação do Professor | Componente Comparativo | EPIC-07 | P1 | 5 SP | Lote 5 |
| `FE-043` | Desenvolver Mural de Avisos da Turma com Filtro por Disciplina | `/mural` | EPIC-08 | P1 | 3 SP | Lote 5 |
| `FE-044` | Criar Interface para Aluno Solicitar Ajuda Pedagógica Confidencial | `/ajuda/solicitar` | EPIC-08 | P0 | 3 SP | Lote 5 |
| `FE-045` | Criar Painel do Professor para Gerenciar e Responder Pedidos de Ajuda | `/professor/solicitacoes` | EPIC-08 | P0 | 3 SP | Lote 5 |
| `FE-046` | Criar Interface Segura para Registro de Observações Pedagógicas Restritas | Modal Observações | EPIC-08 | P0 | 3 SP | Lote 5 |
| `FE-047` | Desenvolver Painel de Gamificação e Conquistas (Badges) do Aluno | `/aluno/conquistas` | EPIC-09 | P2 | 3 SP | Lote 5 |
| `FE-048` | Desenvolver Central de Exportação de Relatórios da Turma (PDF / CSV) | `/relatorios` | EPIC-10 | P1 | 3 SP | Lote 5 |
| `FE-049` | Implementar Tratamento de Acessibilidade (Atalhos de Teclado e Leitor de Tela) | Global A11y | EPIC-10 | P1 | 3 SP | Lote 5 |
| `FE-050` | Implementar Suíte de Testes End-to-End (E2E) dos Fluxos Críticos com Playwright | Testes E2E | EPIC-10 | P0 | 5 SP | Lote 5 |

---

*(Arquivo completo detalhado com todos os componentes, props TypeScript, estados visuais e critérios de aceitação para cada um dos 50 cards de front-end salvo integralmente em `docs/backlog/03-front-end.md`)*
