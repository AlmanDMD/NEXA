# 💻 Backlog de Front-end (Interface & UX) — Projeto NEXA
## 50 Cards Exclusivos e Encadeados de Engenharia de Front-end (`FE-001` a `FE-050`)

Este documento contém o planejamento completo e 100% interligado da interface React + TypeScript + Tailwind CSS do **Sistema Inteligente de Monitoramento do Desempenho Acadêmico — SENAI (NEXA)**, integrado aos endpoints de Back-end (`BE-001`..`BE-050`).

---

### Resumo dos Lotes / Sprints de Implementação
- **Lote 1 / Sprint 1 (FE-001 a FE-010)**: Setup Vite + React + TS, Design System Industrial SENAI, AppShell Responsivo, AuthContext e Fluxo de Login/RBAC.
- **Lote 2 / Sprint 2 (FE-011 a FE-020)**: Telas Administrativas de Cursos, Turmas, Módulos Práticos, Matriz Visual de Competências e Matrícula com Importação CSV.
- **Lote 3 / Sprint 3 (FE-021 a FE-030)**: Diário de Classe Digital, Chamada Rápida, Criação de Tarefas de Oficina, Avaliação por Rubrica Interativa e Planilha de Notas.
- **Lote 4 / Sprint 4 (FE-031 a FE-040)**: Wizard de Autoavaliação do Aluno, Gráfico Radar Comparativo, Dashboard Híbrido do Professor, Alertas Explicáveis e Visão 360°.
- **Lote 5 / Sprint 5 (FE-041 a FE-050)**: Mural da Turma, Canal Seguro "Pedir Ajuda", Diário Confidencial Docente, Galeria de Conquistas, Exportação de Relatórios, Acessibilidade WCAG AA e Testes E2E Playwright.

---

### Tabela Geral Encadeada (50 Cards)

| ID | Título | Epic | Prioridade | Estimativa | Lote / Sprint | Dependências |
|---|---|---|---|---|---|---|
| `FE-001` | Configurar Design System Base e Tokens de Cores SENAI no Tailwind v4 | EPIC-01 | P0 | 3 SP | Lote 1 (S1) | `Nenhuma` |
| `FE-002` | Criar Biblioteca de Componentes Primitivos: Botões, Badges e Tags | EPIC-01 | P0 | 3 SP | Lote 1 (S1) | `FE-001` |
| `FE-003` | Criar Componentes de Formulário com Validação Visual e Acessibilidade | EPIC-01 | P0 | 3 SP | Lote 1 (S1) | `FE-001` |
| `FE-004` | Criar Componente de Modal, Dialog e Confirmação com Foco Acessível | EPIC-01 | P0 | 2 SP | Lote 1 (S1) | `FE-002` |
| `FE-005` | Criar Componentes de Tabela de Dados com Paginação, Ordenação e Busca | EPIC-01 | P0 | 5 SP | Lote 1 (S1) | `FE-002` |
| `FE-006` | Implementar Estados Visuais Padrão: Skeleton Loading, Erro e Vazio (Empty State) | EPIC-01 | P0 | 3 SP | Lote 1 (S1) | `FE-001, FE-002` |
| `FE-007` | Desenvolver Layout Principal (Header com Notificações e Perfil do Usuário) | EPIC-01 | P0 | 3 SP | Lote 1 (S1) | `FE-001, FE-002` |
| `FE-008` | Desenvolver Sidebar Retrátil com Navegação Dinâmica Baseada em Papéis (RBAC) | EPIC-01 | P0 | 3 SP | Lote 1 (S1) | `FE-001, FE-002` |
| `FE-009` | Configurar React Router DOM com Rotas Públicas, Privadas e Guardas de Acesso | EPIC-01 | P0 | 3 SP | Lote 1 (S1) | `FE-007, FE-008` |
| `FE-010` | Criar Cliente HTTP Axios/Fetch Centralizado com Tratamento de Sessão e Toasts | EPIC-01 | P0 | 3 SP | Lote 1 (S1) | `FE-009` |
| `FE-011` | Desenvolver Tela de Login Responsiva com Feedback de Validação | EPIC-01 | P0 | 3 SP | Lote 2 (S2) | `FE-002, FE-003, FE-010` |
| `FE-012` | Implementar Contexto Global de Autenticação (AuthContext) com Persistência | EPIC-01 | P0 | 3 SP | Lote 2 (S2) | `FE-010, FE-011` |
| `FE-013` | Criar Tela de Visualização e Edição de Perfil do Usuário | EPIC-01 | P1 | 2 SP | Lote 2 (S2) | `FE-003, FE-012` |
| `FE-014` | Desenvolver Painel Administrativo de Listagem e Gestão de Usuários | EPIC-01 | P0 | 5 SP | Lote 2 (S2) | `FE-005, FE-008` |
| `FE-015` | Criar Modal de Criação e Edição de Usuários com Definição de Papéis | EPIC-01 | P0 | 3 SP | Lote 2 (S2) | `FE-004, FE-014` |
| `FE-016` | Desenvolver Tela de Gerenciamento de Turmas e Períodos Letivos | EPIC-02 | P0 | 5 SP | Lote 2 (S2) | `FE-002, FE-005` |
| `FE-017` | Criar Tela de Gerenciamento de Disciplinas e Matriz Curricular | EPIC-02 | P0 | 3 SP | Lote 2 (S2) | `FE-005, FE-016` |
| `FE-018` | Desenvolver Interface de Módulos Práticos SENAI (Metrologia, Usinagem) | EPIC-02 | P0 | 3 SP | Lote 2 (S2) | `FE-017` |
| `FE-019` | Criar Tela de Gestão de Matrículas e Vínculo de Estudantes à Turma | EPIC-02 | P0 | 5 SP | Lote 2 (S2) | `FE-005, FE-016` |
| `FE-020` | Criar Tela de Associação de Professores às Turmas e Oficinas | EPIC-02 | P1 | 3 SP | Lote 2 (S2) | `FE-016, FE-017, BE-018, DB-018` |
| `FE-021` | Desenvolver Diário de Classe: Visão Geral de Aulas da Disciplina | EPIC-03 | P0 | 3 SP | Lote 3 (S3) | `FE-004, FE-005, FE-018, BE-021, DB-021` |
| `FE-022` | Criar Interface de Chamada Rápida de Frequência em 1 Clique (Matriz da Turma) | EPIC-03 | P0 | 5 SP | Lote 3 (S3) | `FE-002, FE-019, FE-021, BE-022, DB-022` |
| `FE-023` | Implementar Indicador Visual de Presença/Faltas com Alerta de Limite 75% | EPIC-03 | P0 | 3 SP | Lote 3 (S3) | `FE-002, FE-022, BE-023, DB-037` |
| `FE-024` | Criar Painel de Cadastro e Listagem de Atividades Práticas de Oficina | EPIC-04 | P0 | 3 SP | Lote 3 (S3) | `FE-004, FE-018, BE-015, BE-024, DB-023, DB-024` |
| `FE-025` | Desenvolver Componente de Registro Rápido de Conclusão Prática pelo Docente | EPIC-04 | P0 | 5 SP | Lote 3 (S3) | `FE-005, FE-024, BE-025, DB-025` |
| `FE-026` | Criar Modal de Avaliação por Rubricas de Habilidade Técnica (Tolerâncias/Acabamento) | EPIC-04 | P1 | 5 SP | Lote 3 (S3) | `FE-004, FE-025, BE-025, DB-024, DB-026` |
| `FE-027` | Desenvolver Tela de Lançamento de Notas de Avaliações e Provas | EPIC-03 | P0 | 5 SP | Lote 3 (S3) | `FE-003, FE-005, BE-027, DB-027, DB-028` |
| `FE-028` | Criar Visualizador de Médias e Histórico Parcial por Aluno e Turma | EPIC-03 | P0 | 3 SP | Lote 3 (S3) | `FE-005, FE-027, BE-028, DB-028` |
| `FE-029` | Implementar Filtros Avançados por Disciplina, Módulo e Período nas Tabelas | EPIC-03 | P1 | 2 SP | Lote 3 (S3) | `FE-003, FE-005, FE-009` |
| `FE-030` | Testes Unitários de Componentes de Lançamento de Notas e Frequência | EPIC-03 | P0 | 3 SP | Lote 3 (S3) | `FE-021, FE-022, FE-023, FE-024, FE-025, FE-026, FE-027, FE-028, FE-029, BE-030` |
| `FE-031` | Desenvolver Dashboard do Professor: Visão Geral e Indicadores-Chave (KPIs) | EPIC-05 | P0 | 5 SP | Lote 4 (S4) | `FE-006, FE-028, FE-029, BE-031, DB-036` |
| `FE-032` | Criar Card de Aluno em Risco Acadêmico com Motivo Explicável e Ação Rápida | EPIC-05 | P0 | 3 SP | Lote 4 (S4) | `FE-004, FE-031, BE-032, BE-033, BE-039, DB-034` |
| `FE-033` | Criar Gráfico de Evolução de Habilidades e Desempenho da Turma | EPIC-05 | P1 | 5 SP | Lote 4 (S4) | `FE-001, FE-031, BE-031, DB-036` |
| `FE-034` | Desenvolver Visão 360° do Aluno (Ficha Completa: Notas, Faltas e Habilidades) | EPIC-05 | P0 | 5 SP | Lote 4 (S4) | `FE-009, FE-023, FE-031, FE-032, BE-031, DB-036` |
| `FE-035` | Desenvolver Portal de Autonomia do Aluno (Visão Inicial do Estudante) | EPIC-06 | P0 | 5 SP | Lote 4 (S4) | `FE-008, FE-012, BE-034, DB-036` |
| `FE-036` | Criar Painel de Tarefas Pendentes, Concluídas e Atrasadas do Estudante | EPIC-06 | P0 | 3 SP | Lote 4 (S4) | `FE-006, FE-026, FE-035, BE-026, DB-025` |
| `FE-037` | Desenvolver Visualização de Notas e Frequência do Próprio Aluno | EPIC-06 | P0 | 3 SP | Lote 4 (S4) | `FE-023, FE-035, BE-023, BE-034, DB-028, DB-037` |
| `FE-038` | Criar Gráfico Radar de Competências Técnicas do Aluno (Ex: Tornearia, Fresamento) | EPIC-06 | P1 | 5 SP | Lote 4 (S4) | `FE-034, FE-035, BE-034, BE-038, DB-015, DB-033` |
| `FE-039` | Desenvolver Linha do Tempo de Conquistas e Marcos Acadêmicos | EPIC-06 | P2 | 3 SP | Lote 4 (S4) | `FE-035, BE-034, DB-039` |
| `FE-040` | Implementar Responsividade Mobile do Dashboard e Portal do Aluno | EPIC-06 | P0 | 3 SP | Lote 4 (S4) | `FE-007, FE-008, FE-031, FE-034, FE-035, FE-036, FE-037, FE-038` |
| `FE-041` | Desenvolver Interface de Autoavaliação de Domínio de Habilidades Práticas | EPIC-07 | P1 | 5 SP | Lote 5 (S5) | `FE-003, FE-035, BE-035, BE-036, DB-031, DB-032` |
| `FE-042` | Criar Componente Comparativo Visual: Autoavaliação vs Avaliação do Professor | EPIC-07 | P1 | 5 SP | Lote 5 (S5) | `FE-034, FE-038, FE-041, BE-037, BE-038, DB-035, DB-038` |
| `FE-043` | Desenvolver Mural de Avisos da Turma com Filtro por Disciplina | EPIC-08 | P1 | 3 SP | Lote 5 (S5) | `FE-002, FE-004, FE-029, BE-041, BE-042, DB-041` |
| `FE-044` | Criar Interface para Aluno Solicitar Ajuda Pedagógica Confidencial | EPIC-08 | P0 | 3 SP | Lote 5 (S5) | `FE-003, FE-035, BE-043, BE-044, DB-042, DB-044` |
| `FE-045` | Criar Painel do Professor para Gerenciar e Responder Pedidos de Ajuda | EPIC-08 | P0 | 3 SP | Lote 5 (S5) | `FE-007, FE-034, FE-044, BE-043, BE-044, DB-042, DB-044` |
| `FE-046` | Criar Interface Segura para Registro de Observações Pedagógicas Restritas | EPIC-08 | P0 | 3 SP | Lote 5 (S5) | `FE-004, FE-034, BE-045, DB-043` |
| `FE-047` | Desenvolver Painel de Gamificação e Conquistas (Badges) do Aluno | EPIC-09 | P2 | 3 SP | Lote 5 (S5) | `FE-035, FE-039, BE-046, BE-047, DB-045, DB-046` |
| `FE-048` | Desenvolver Central de Exportação de Relatórios da Turma (PDF / CSV) | EPIC-10 | P1 | 3 SP | Lote 5 (S5) | `FE-005, FE-029, FE-031, BE-048, BE-049, DB-047` |
| `FE-049` | Implementar Tratamento de Acessibilidade (Atalhos de Teclado e Leitor de Tela) | EPIC-10 | P1 | 3 SP | Lote 5 (S5) | `FE-001, FE-003, FE-004, FE-022, FE-027, FE-040, FE-041` |
| `FE-050` | Implementar Suíte de Testes End-to-End (E2E) dos Fluxos Críticos com Playwright | EPIC-10 | P0 | 5 SP | Lote 5 (S5) | `FE-001, FE-010, FE-020, FE-030, FE-040, FE-042, FE-045, FE-048, FE-049, BE-050, DB-050` |

---

## Detalhamento Completo e Encadeado dos 50 Cards

### [FE-001] Configurar Design System Base e Tokens de Cores SENAI no Tailwind v4
- **ID**: `FE-001`
- **Título**: Configurar Design System Base e Tokens de Cores SENAI no Tailwind v4
- **Área**: Front-end
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `Início da Trilha` | ➡️ Próximo: `FE-002`
- **Dependências Diretas**: `Nenhuma`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: infraestrutura
- **Objetivo**: Implementar a identidade visual institucional e tokens de design no Tailwind CSS v4 para garantir consistência estética em todas as telas.
- **Descrição**: Configurar a paleta de cores institucional (Vermelho SENAI, Azul Petróleo, Neutros escuros e claros), tipografia Inter/Outfit, raios de borda e sombras consistentes no CSS global com as diretivas do Tailwind v4 (@theme).
- **História de Usuário**: Como Usuário do Sistema, quero navegar em uma interface moderna, elegante e alinhada à identidade visual do SENAI, com alto contraste e legibilidade.
- **Critérios de Aceitação**:
- Variáveis de cores definidas no Tailwind v4: primary (SENAI Red), secondary (Navy), surface, background, text-muted.
- Suporte a modo escuro/claro com variáveis semânticas.
- Fontes Google Fonts (Inter) importadas e renderizando corretamente.
- **Definição de Pronto (DoD)**: Telas de teste exibem cores e tipografia corretas sem estilos ad-hoc.
- **Observações Técnicas**: Tailwind v4 utiliza @theme no CSS principal ao invés de tailwind.config.js.

---

### [FE-002] Criar Biblioteca de Componentes Primitivos: Botões, Badges e Tags
- **ID**: `FE-002`
- **Título**: Criar Biblioteca de Componentes Primitivos: Botões, Badges e Tags
- **Área**: Front-end
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `FE-001` | ➡️ Próximo: `FE-003`
- **Dependências Diretas**: `FE-001`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Disponibilizar componentes atômicos reutilizáveis com múltiplos estados visuais para acelerar o desenvolvimento das telas.
- **Descrição**: Criar componentes em src/components/ui: Button (variantes: primary, secondary, outline, ghost, danger; tamanhos: sm, md, lg; suporte a loading spinner e ícone Lucide), Badge (status: success, warning, danger, info) e Tag.
- **História de Usuário**: Como Desenvolvedor Front-end, quero usar componentes de botão e badges padronizados, para manter uniformidade em botões de ação e status.
- **Critérios de Aceitação**:
- Button com tipagem TypeScript completa (ButtonProps estendendo HTMLButtonElement).
- Estado disabled e isLoading desabilitando cliques e mostrando spinner.
- Badges com cores contrastantes segundo padrão WCAG.
- **Definição de Pronto (DoD)**: Componentes exportados e testados em página de demonstração/storyboard.
- **Observações Técnicas**: Utilizar clsx e tailwind-merge para composição limpa de classes CSS.

---

### [FE-003] Criar Componentes de Formulário com Validação Visual e Acessibilidade
- **ID**: `FE-003`
- **Título**: Criar Componentes de Formulário com Validação Visual e Acessibilidade
- **Área**: Front-end
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `FE-002` | ➡️ Próximo: `FE-004`
- **Dependências Diretas**: `FE-001`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Desenvolver campos de formulário reutilizáveis integrados com mensagens de erro e labels acessíveis.
- **Descrição**: Criar componentes em src/components/forms: InputText, InputPassword (com botão mostrar/ocultar senha), Select, Checkbox e Textarea. Suporte a label flutuante ou superior, indicação de campo obrigatório e borda vermelha em caso de erro.
- **História de Usuário**: Como Usuário, quero ver orientações claras quando errar o preenchimento de um campo, para corrigir meus dados facilmente.
- **Critérios de Aceitação**:
- Todos os inputs aceitam prop error com mensagem explicativa renderizada abaixo do campo.
- InputPassword alterna visualização de caracteres com ícones Eye e EyeOff.
- Atributos aria-invalid e aria-describedby configurados para acessibilidade.
- **Definição de Pronto (DoD)**: Componentes funcionando e integráveis com React Hook Form.
- **Observações Técnicas**: Garantir que IDs sejam gerados automaticamente via useId() do React para vincular labels.

---

### [FE-004] Criar Componente de Modal, Dialog e Confirmação com Foco Acessível
- **ID**: `FE-004`
- **Título**: Criar Componente de Modal, Dialog e Confirmação com Foco Acessível
- **Área**: Front-end
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `FE-003` | ➡️ Próximo: `FE-005`
- **Dependências Diretas**: `FE-002`
- **Prioridade**: P0 | **Estimativa**: 2 SP | **Tipo**: feature
- **Objetivo**: Implementar caixas de diálogo modais para confirmação de ações destrutivas e formulários rápidos em popup.
- **Descrição**: Desenvolver src/components/ui/Modal com backdrop translúcido com desfoque (backdrop-blur-sm), animação suave de entrada/saída, botão de fechar, travamento de rolagem do body e captura de tecla ESC.
- **História de Usuário**: Como Usuário, quero ser solicitado a confirmar ações críticas (ex: trancar matrícula, excluir item), para evitar cliques acidentais.
- **Critérios de Aceitação**:
- Modal fecha ao pressionar tecla ESC ou clicar no backdrop.
- Foco do teclado preso dentro do modal enquanto estiver aberto (focus trap).
- Variação ConfirmDialog pronta para confirmações rápidas com botões Cancelar e Confirmar.
- **Definição de Pronto (DoD)**: Componente modal testado em desktop e mobile com acessibilidade de teclado.
- **Observações Técnicas**: Pode ser renderizado via React Portal em #modal-root para evitar problemas de z-index.

---

### [FE-005] Criar Componentes de Tabela de Dados com Paginação, Ordenação e Busca
- **ID**: `FE-005`
- **Título**: Criar Componentes de Tabela de Dados com Paginação, Ordenação e Busca
- **Área**: Front-end
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `FE-004` | ➡️ Próximo: `FE-006`
- **Dependências Diretas**: `FE-002`
- **Prioridade**: P0 | **Estimativa**: 5 SP | **Tipo**: feature
- **Objetivo**: Construir uma tabela de dados avançada e responsiva para listagem de alunos, turmas, notas e presenças.
- **Descrição**: Criar src/components/tables/DataTable genérico com TypeScript. Suporte a colunas customizáveis com renderizadores de célula, clique no cabeçalho para ordenação asc/desc, barra de busca rápida com debounce e rodapé de paginação (Página anterior, próxima e seletor de itens por página).
- **História de Usuário**: Como Professor ou Coordenador, quero ordenar e pesquisar registros em tabelas extensas, para localizar rapidamente o aluno ou turma desejada.
- **Critérios de Aceitação**:
- Tabela responsiva com rolagem horizontal em telas pequenas sem quebrar o layout.
- Indicadores visuais de ordenação (setas para cima/baixo na coluna ativa).
- Suporte a estados de carregamento e estado vazio nativos.
- **Definição de Pronto (DoD)**: Componente DataTable tipado genericamente <TData> e testado com mock de dados.
- **Observações Técnicas**: Permitir integração com TanStack Table se necessário para alta complexidade.

---

### [FE-006] Implementar Estados Visuais Padrão: Skeleton Loading, Erro e Vazio (Empty State)
- **ID**: `FE-006`
- **Título**: Implementar Estados Visuais Padrão: Skeleton Loading, Erro e Vazio (Empty State)
- **Área**: Front-end
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `FE-005` | ➡️ Próximo: `FE-007`
- **Dependências Diretas**: `FE-001, FE-002`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Prover feedback visual agradável durante carregamentos de dados ou quando não houver registros a exibir.
- **Descrição**: Desenvolver componentes em src/components/feedback: Skeleton (com animação shimmer pulsante para cards e linhas de tabela), EmptyState (ilustração/ícone amigável, título, descrição e botão de ação primária) e ErrorState (alerta com botão de 'Tentar novamente').
- **História de Usuário**: Como Usuário, quero ver esqueletos de carregamento ao invés de telas brancas travadas, para saber que o sistema está processando minhas informações.
- **Critérios de Aceitação**:
- Skeleton anima suavemente simulando o conteúdo que será carregado.
- EmptyState exibido quando arrays de turmas/alunos retornarem vazios.
- ErrorState renderiza botão que executa função retry repassada via prop.
- **Definição de Pronto (DoD)**: Componentes criados e integrados com as views do Lote 1.
- **Observações Técnicas**: Melhora significativa da métrica de Perceived Performance.

---

### [FE-007] Desenvolver Layout Principal (Header com Notificações e Perfil do Usuário)
- **ID**: `FE-007`
- **Título**: Desenvolver Layout Principal (Header com Notificações e Perfil do Usuário)
- **Área**: Front-end
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `FE-006` | ➡️ Próximo: `FE-008`
- **Dependências Diretas**: `FE-001, FE-002`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Criar o cabeçalho superior da aplicação autenticada com navegação rápida, notificações e menu de perfil.
- **Descrição**: Implementar src/layouts/AppHeader contendo logo SENAI, seletor de turma ativa (para professores), sino de notificações com badge de contagem, dropdown de usuário com foto/avatar, nome, matrícula e botão de Sair (Logout).
- **História de Usuário**: Como Usuário Logado, quero ter um cabeçalho fixo com acesso rápido ao meu perfil e avisos, para me orientar facilmente dentro da plataforma.
- **Critérios de Aceitação**:
- Header responsivo fixado no topo (sticky top-0).
- Dropdown de perfil abre e fecha suavemente com clique fora.
- Exibe nome do usuário autenticado vindo do contexto.
- **Definição de Pronto (DoD)**: Header integrado ao layout mestre e adaptado a telas mobile e desktop.
- **Observações Técnicas**: Z-index calibrado para ficar abaixo apenas de modais globais.

---

### [FE-008] Desenvolver Sidebar Retrátil com Navegação Dinâmica Baseada em Papéis (RBAC)
- **ID**: `FE-008`
- **Título**: Desenvolver Sidebar Retrátil com Navegação Dinâmica Baseada em Papéis (RBAC)
- **Área**: Front-end
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `FE-007` | ➡️ Próximo: `FE-009`
- **Dependências Diretas**: `FE-001, FE-002`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Implementar menu lateral que adapta os links exibidos de acordo com o papel do usuário (Aluno, Professor ou Coordenador).
- **Descrição**: Criar src/layouts/Sidebar com suporte a modo colapsado/expandido. Links: Dashboard, Turmas, Diário/Chamada, Oficinas Práticas, Notas, Alertas, Autoavaliação e Mural. Alunos visualizam apenas Portal do Aluno, Minhas Notas, Autoavaliação e Ajuda.
- **História de Usuário**: Como Usuário, quero ver no menu apenas as funcionalidades permitidas para o meu perfil, para não ser exposto a opções que não posso usar.
- **Critérios de Aceitação**:
- Sidebar filtra itens com base em user.role.
- Destaque visual da rota atualmente ativa (active state com cor primária).
- Em telas mobile, transforma-se em menu gaveta (drawer) com botão hambúrguer.
- **Definição de Pronto (DoD)**: Sidebar responsiva e com filtragem de rotas por role testada.
- **Observações Técnicas**: Armazenar preferência de sidebar recolhida no localStorage.

---

### [FE-009] Configurar React Router DOM com Rotas Públicas, Privadas e Guardas de Acesso
- **ID**: `FE-009`
- **Título**: Configurar React Router DOM com Rotas Públicas, Privadas e Guardas de Acesso
- **Área**: Front-end
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `FE-008` | ➡️ Próximo: `FE-010`
- **Dependências Diretas**: `FE-007, FE-008`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Estruturar o roteamento da aplicação com proteção de rotas privadas e redirecionamento de usuários não autorizados.
- **Descrição**: Configurar react-router-dom v7 com createBrowserRouter ou BrowserRouter. Criar componentes ProtectedRoute (redireciona para /login se não autenticado) e RoleRoute (redireciona para /403 se o perfil não tiver permissão).
- **História de Usuário**: Como Usuário Não Autenticado, quero ser redirecionado para a tela de login ao tentar acessar uma URL protegida diretamente pelo navegador.
- **Critérios de Aceitação**:
- Tentativa de acessar rota privada sem autenticação redireciona para /login gravando a rota de origem (from).
- Aluno tentando acessar /admin recebe tela 403 Acesso Negado.
- Rota curinga * renderiza tela 404 Página Não Encontrada.
- **Definição de Pronto (DoD)**: Estrutura de rotas funcionando com guardas de autenticação e RBAC.
- **Observações Técnicas**: Permite carregamento sob demanda (lazy loading) via React.lazy() para otimizar o bundle.

---

### [FE-010] Criar Cliente HTTP Axios/Fetch Centralizado com Tratamento de Sessão e Toasts
- **ID**: `FE-010`
- **Título**: Criar Cliente HTTP Axios/Fetch Centralizado com Tratamento de Sessão e Toasts
- **Área**: Front-end
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `FE-009` | ➡️ Próximo: `FE-011`
- **Dependências Diretas**: `FE-009`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Centralizar todas as requisições à API, renovação automática de token e notificações visuais de sucesso/erro.
- **Descrição**: Criar src/services/api.ts com instância configurada. Implementar interceptors de resposta: se receber 401, pausa requisições, chama endpoint /refresh e refaz a requisição original; se falhar, redireciona para login. Integrar com biblioteca de toasts (ex: Sonner ou React Hot Toast) para alertas.
- **História de Usuário**: Como Desenvolvedor Front-end, quero chamar api.get('/courses') sem me preocupar com anexar tokens ou tratar expiração manualmente.
- **Critérios de Aceitação**:
- Anexa automaticamente Authorization: Bearer <token> se logado.
- Renovação transparente de token em erros 401 usando fila de requests pendentes.
- Exibe toast de erro quando a API retornar 500 ou erro de conexão.
- **Definição de Pronto (DoD)**: Cliente HTTP configurado e testado com mock de renovação de token.
- **Observações Técnicas**: Prevenir loops infinitos de renovação se a rota de refresh retornar 401.

---

### [FE-011] Desenvolver Tela de Login Responsiva com Feedback de Validação
- **ID**: `FE-011`
- **Título**: Desenvolver Tela de Login Responsiva com Feedback de Validação
- **Área**: Front-end
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 2 (S2)
- **Sequência na Squad**: ⬅️ Anterior: `FE-010` | ➡️ Próximo: `FE-012`
- **Dependências Diretas**: `FE-002, FE-003, FE-010`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Criar a interface visual de autenticação do sistema com foco na usabilidade e segurança.
- **Descrição**: Desenvolver a tela /login contendo card centralizado com logo SENAI, campos de E-mail institucional e Senha, link de 'Esqueci minha senha', botão de Entrar com estado de loading, e mensagens de alerta amigáveis em caso de erro.
- **História de Usuário**: Como Usuário, quero digitar minhas credenciais e receber feedback imediato de validação, para acessar o sistema com clareza.
- **Critérios de Aceitação**:
- Validação local de e-mail (formato correto) e senha preenchida antes do envio.
- Desabilita botão e mostra spinner durante a requisição de login.
- Exibe mensagem clara em caso de credenciais inválidas.
- **Definição de Pronto (DoD)**: Tela de login funcional, responsiva e integrada à rota /login.
- **Observações Técnicas**: Garantir compatibilidade com preenchimento automático (autofill) dos navegadores.

---

### [FE-012] Implementar Contexto Global de Autenticação (AuthContext) com Persistência
- **ID**: `FE-012`
- **Título**: Implementar Contexto Global de Autenticação (AuthContext) com Persistência
- **Área**: Front-end
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 2 (S2)
- **Sequência na Squad**: ⬅️ Anterior: `FE-011` | ➡️ Próximo: `FE-013`
- **Dependências Diretas**: `FE-010, FE-011`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Gerenciar o estado de login, usuário atual e permissões em toda a árvore de componentes React.
- **Descrição**: Criar src/contexts/AuthContext.tsx com hook useAuth(). Métodos expostos: login(email, password), logout(), user, isAuthenticated, isLoading. Na montagem do app, consulta /api/v1/auth/me para restaurar sessão ativa sem piscar a tela.
- **História de Usuário**: Como Desenvolvedor Front-end, quero usar const { user, logout } = useAuth() em qualquer tela, para acessar os dados do usuário corrente.
- **Critérios de Aceitação**:
- Hook useAuth() lança erro se usado fora do AuthProvider.
- Estado isLoading = true enquanto valida a sessão inicial.
- Redirecionamento automático pós-login para a página correspondente ao perfil.
- **Definição de Pronto (DoD)**: Contexto implementado com testes de alternância de estado de login/logout.
- **Observações Técnicas**: Evitar armazenar tokens JWT no localStorage por vulnerabilidade a XSS; usar cookies HttpOnly + estado em memória.

---

### [FE-013] Criar Tela de Visualização e Edição de Perfil do Usuário
- **ID**: `FE-013`
- **Título**: Criar Tela de Visualização e Edição de Perfil do Usuário
- **Área**: Front-end
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 2 (S2)
- **Sequência na Squad**: ⬅️ Anterior: `FE-012` | ➡️ Próximo: `FE-014`
- **Dependências Diretas**: `FE-003, FE-012`
- **Prioridade**: P1 | **Estimativa**: 2 SP | **Tipo**: feature
- **Objetivo**: Permitir que alunos e professores consultem seus dados cadastrais, matrícula SENAI e atualizem informações de contato.
- **Descrição**: Desenvolver rota /perfil contendo: foto/avatar com opção de upload, nome completo, matrícula institucional (somente leitura), e-mail, telefone de contato e botão para alteração de senha com confirmação.
- **História de Usuário**: Como Estudante ou Professor, quero visualizar meus dados acadêmicos e atualizar meu telefone, para manter meus contatos em dia com a instituição.
- **Critérios de Aceitação**:
- Campos institucionais críticos (matrícula, papel) desabilitados para edição direta pelo aluno.
- Formulário de alteração de senha exige senha atual e confirmação da nova senha.
- Feedback visual toast de sucesso ao salvar alterações.
- **Definição de Pronto (DoD)**: Tela funcional e integrada com endpoint de perfil do usuário.
- **Observações Técnicas**: Validar força da nova senha no cliente antes da submissão.

---

### [FE-014] Desenvolver Painel Administrativo de Listagem e Gestão de Usuários
- **ID**: `FE-014`
- **Título**: Desenvolver Painel Administrativo de Listagem e Gestão de Usuários
- **Área**: Front-end
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 2 (S2)
- **Sequência na Squad**: ⬅️ Anterior: `FE-013` | ➡️ Próximo: `FE-015`
- **Dependências Diretas**: `FE-005, FE-008`
- **Prioridade**: P0 | **Estimativa**: 5 SP | **Tipo**: feature
- **Objetivo**: Disponibilizar aos coordenadores e administradores uma visão consolidada de todos os usuários do sistema.
- **Descrição**: Criar rota /admin/usuarios utilizando o componente DataTable. Exibe: Avatar, Nome, E-mail, Matrícula SENAI, Papel (com Badges coloridas por perfil), Status (Ativo/Inativo) e menu de ações (Editar, Resetar Senha, Desativar).
- **História de Usuário**: Como Coordenador, quero filtrar e buscar usuários por nome, matrícula ou papel, para gerenciar acessos à plataforma.
- **Critérios de Aceitação**:
- Barra de busca com debounce filtrando por nome e e-mail.
- Filtro dropdown por Role (Todos, Alunos, Professores, Coordenadores).
- Ações de desativação abrem modal de confirmação.
- **Definição de Pronto (DoD)**: Tela administrativa funcional com dados reais ou mockados.
- **Observações Técnicas**: Acesso estritamente bloqueado para usuários que não sejam ADMIN ou COORDINATOR.

---

### [FE-015] Criar Modal de Criação e Edição de Usuários com Definição de Papéis
- **ID**: `FE-015`
- **Título**: Criar Modal de Criação e Edição de Usuários com Definição de Papéis
- **Área**: Front-end
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 2 (S2)
- **Sequência na Squad**: ⬅️ Anterior: `FE-014` | ➡️ Próximo: `FE-016`
- **Dependências Diretas**: `FE-004, FE-014`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Interface para cadastro rápido de novos alunos, instrutores ou coordenadores.
- **Descrição**: Implementar modal com formulário: Nome completo, E-mail institucional, Matrícula SENAI, Papel institucional (Select), Telefone e opção de gerar senha temporária com envio de e-mail de boas-vindas.
- **História de Usuário**: Como Administrador, quero cadastrar um novo instrutor pelo modal, para conceder acesso imediato ao lançamento de aulas.
- **Critérios de Aceitação**:
- Validação de e-mail único e formato institucional.
- Desabilita botão e exibe loading durante cadastro.
- Atualiza a listagem da tabela automaticamente após salvar com sucesso.
- **Definição de Pronto (DoD)**: Modal testado e integrado com a tela de gestão de usuários.
- **Observações Técnicas**: Garantir foco automático no primeiro input ao abrir o modal.

---

### [FE-016] Desenvolver Tela de Gerenciamento de Turmas e Períodos Letivos
- **ID**: `FE-016`
- **Título**: Desenvolver Tela de Gerenciamento de Turmas e Períodos Letivos
- **Área**: Front-end
- **Epic**: EPIC-02: Gestão Acadêmica & Estrutura SENAI
- **Lote / Sprint**: Lote 2 (S2)
- **Sequência na Squad**: ⬅️ Anterior: `FE-015` | ➡️ Próximo: `FE-017`
- **Dependências Diretas**: `FE-002, FE-005`
- **Prioridade**: P0 | **Estimativa**: 5 SP | **Tipo**: feature
- **Objetivo**: Interface para coordenadores visualizarem e criarem turmas do semestre.
- **Descrição**: Criar rota /turmas com visualização em Grid de Cards ou Tabela. Cada card de turma exibe: Código da Turma (ex: MEC-2026-1T), Curso Técnico, Turno, Quantidade de Alunos Matriculados vs Capacidade Máxima (com barra de progresso visual) e Status.
- **História de Usuário**: Como Coordenador, quero visualizar as turmas ativas do semestre e sua lotação, para planejar a ocupação dos laboratórios de oficina.
- **Critérios de Aceitação**:
- Barra de progresso indica lotação (verde: <80%, amarelo: 80-99%, vermelho: 100% lotada).
- Botão 'Nova Turma' abrindo formulário de criação.
- Clique no card navega para a visão detalhada da turma.
- **Definição de Pronto (DoD)**: Tela de turmas implementada e responsiva.
- **Observações Técnicas**: Implementar filtros por turno (Manhã, Tarde, Noite) e período letivo.

---

### [FE-017] Criar Tela de Gerenciamento de Disciplinas e Matriz Curricular
- **ID**: `FE-017`
- **Título**: Criar Tela de Gerenciamento de Disciplinas e Matriz Curricular
- **Área**: Front-end
- **Epic**: EPIC-02: Gestão Acadêmica & Estrutura SENAI
- **Lote / Sprint**: Lote 2 (S2)
- **Sequência na Squad**: ⬅️ Anterior: `FE-016` | ➡️ Próximo: `FE-018`
- **Dependências Diretas**: `FE-005, FE-016`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Interface para consulta e estruturação das unidades curriculares dos cursos.
- **Descrição**: Desenvolver rota /disciplinas exibindo acordeão ou lista hierárquica por curso técnico. Cada disciplina detalha: Código, Nome, Carga horária total e lista de módulos práticos vinculados.
- **História de Usuário**: Como Coordenador Pedagógico, quero visualizar as disciplinas e seus módulos práticos, para garantir que o currículo do curso esteja completo.
- **Critérios de Aceitação**:
- Exibe disciplinas agrupadas por curso técnico selecionado.
- Botão de cadastro e edição de disciplinas.
- Indicador visual de disciplinas que possuem módulos práticos de oficina.
- **Definição de Pronto (DoD)**: Tela funcional e integrada aos endpoints de disciplinas.
- **Observações Técnicas**: Permitir expandir e recolher módulos de cada disciplina.

---

### [FE-018] Desenvolver Interface de Módulos Práticos SENAI (Metrologia, Usinagem)
- **ID**: `FE-018`
- **Título**: Desenvolver Interface de Módulos Práticos SENAI (Metrologia, Usinagem)
- **Área**: Front-end
- **Epic**: EPIC-02: Gestão Acadêmica & Estrutura SENAI
- **Lote / Sprint**: Lote 2 (S2)
- **Sequência na Squad**: ⬅️ Anterior: `FE-017` | ➡️ Próximo: `FE-019`
- **Dependências Diretas**: `FE-017`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Tela especializada na configuração de módulos de aprendizagem prática de oficina.
- **Descrição**: Criar rota /modulos permitindo visualizar a ordem didática dos módulos práticos (ex: 1º Desenho Técnico, 2º Metrologia com Paquímetro, 3º Tornearia Básica). Exibe horas práticas de oficina, nota de corte e competências associadas.
- **História de Usuário**: Como Instrutor SENAI, quero consultar a sequência de módulos práticos e suas competências, para planejar as tarefas de máquina e bancada.
- **Critérios de Aceitação**:
- Ordenação visual clara com numeração sequencial dos módulos.
- Lista de competências vinculadas exibidas como tags com seus respectivos níveis.
- Ação de editar detalhes e critérios do módulo.
- **Definição de Pronto (DoD)**: Interface implementada com suporte aos módulos curriculares SENAI.
- **Observações Técnicas**: Prever suporte visual a drag-and-drop para reordenação didática de módulos.

---

### [FE-019] Criar Tela de Gestão de Matrículas e Vínculo de Estudantes à Turma
- **ID**: `FE-019`
- **Título**: Criar Tela de Gestão de Matrículas e Vínculo de Estudantes à Turma
- **Área**: Front-end
- **Epic**: EPIC-02: Gestão Acadêmica & Estrutura SENAI
- **Lote / Sprint**: Lote 2 (S2)
- **Sequência na Squad**: ⬅️ Anterior: `FE-018` | ➡️ Próximo: `FE-020`
- **Dependências Diretas**: `FE-005, FE-016`
- **Prioridade**: P0 | **Estimativa**: 5 SP | **Tipo**: feature
- **Objetivo**: Permitir que a secretaria matricule estudantes em turmas e consulte a lista oficial de alunos daquela classe.
- **Descrição**: Desenvolver rota /turmas/:id/alunos com tabela completa de estudantes matriculados, opção de matricular novo estudante via busca de aluno pelo nome/matrícula e ações para alterar status (Ativo, Trancado).
- **História de Usuário**: Como Secretaria, quero matricular estudantes selecionando-os em uma lista com autocompletar, para preencher a turma com rapidez.
- **Critérios de Aceitação**:
- Campo de busca com autocompletar para localizar alunos não matriculados.
- Validação visual alertando quando a turma atingir a capacidade máxima.
- Tabela de alunos com status da matrícula e data de ingresso.
- **Definição de Pronto (DoD)**: Tela de gestão de matrículas testada e funcional.
- **Observações Técnicas**: Evitar recarregar toda a página ao matricular; atualizar estado localmente.

---

### [FE-020] Criar Tela de Associação de Professores às Turmas e Oficinas
- **ID**: `FE-020`
- **Título**: Criar Tela de Associação de Professores às Turmas e Oficinas
- **Área**: Front-end
- **Epic**: EPIC-02: Gestão Acadêmica & Estrutura SENAI
- **Lote / Sprint**: Lote 2 (S2)
- **Sequência na Squad**: ⬅️ Anterior: `FE-019` | ➡️ Próximo: `FE-021`
- **Dependências Diretas**: `FE-016, FE-017, BE-018, DB-018`
- **Prioridade**: P1 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Interface para coordenadores atribuírem os instrutores responsáveis por cada disciplina e laboratório de oficina.
- **Descrição**: Criar tela em /atribuicoes permitindo selecionar Turma -> Disciplina -> Instrutor Responsável. Exibe lista de atribuições ativas com opção de definir se é o professor titular ou instrutor assistente de oficina.
- **História de Usuário**: Como Coordenador, quero designar qual professor é responsável por cada matéria, para que a pauta correta apareça no diário dele.
- **Critérios de Aceitação**:
- Associação visual de instrutor à turma e matéria com validação.
- Exibição de cards das disciplinas com o professor atribuído.
- Opção de desvincular ou trocar instrutor com modal de confirmação.
- **Definição de Pronto (DoD)**: Tela testada e integrada com endpoint de alocação de docentes.
- **Observações Técnicas**: Permitir múltiplos professores por turma para atender aulas práticas conjuntas.

---

### [FE-021] Desenvolver Diário de Classe: Visão Geral de Aulas da Disciplina
- **ID**: `FE-021`
- **Título**: Desenvolver Diário de Classe: Visão Geral de Aulas da Disciplina
- **Área**: Front-end
- **Epic**: EPIC-03: Diário de Classe: Notas & Frequência
- **Lote / Sprint**: Lote 3 (S3)
- **Sequência na Squad**: ⬅️ Anterior: `FE-020` | ➡️ Próximo: `FE-022`
- **Dependências Diretas**: `FE-004, FE-005, FE-018, BE-021, DB-021`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Construir a tela /aulas para o professor listar as aulas ministradas por turma/módulo e registrar um novo encontro letivo.
- **Descrição**: Implementar interface com seletor de Turma, Disciplina e Módulo Prático (ex: Metrologia, Tornearia), botão 'Registrar Nova Aula' abrindo modal com data, horas-aula (1 a 8h), ambiente/laboratório utilizado e resumo do conteúdo ministrado, além de atalho direto para 'Fazer Chamada'.
- **História de Usuário**: Como Professor, quero visualizar o cronograma de aulas ministradas da minha turma e abrir a aula do dia em segundos.
- **Critérios de Aceitação**:
- Lista aulas cronologicamente indicando se a chamada já foi realizada ou está pendente.
- Formulário valida campos obrigatórios e consome POST /api/v1/lessons (BE-021).
- Exibe estados Skeleton Loading e Empty State (FE-006).
- **Definição de Pronto (DoD)**: Tela /aulas funcional e integrada com BE-021.
- **Observações Técnicas**: Desbloqueia diretamente a tela de chamada rápida (FE-022).

---

### [FE-022] Criar Interface de Chamada Rápida de Frequência em 1 Clique (Matriz da Turma)
- **ID**: `FE-022`
- **Título**: Criar Interface de Chamada Rápida de Frequência em 1 Clique (Matriz da Turma)
- **Área**: Front-end
- **Epic**: EPIC-03: Diário de Classe: Notas & Frequência
- **Lote / Sprint**: Lote 3 (S3)
- **Sequência na Squad**: ⬅️ Anterior: `FE-021` | ➡️ Próximo: `FE-023`
- **Dependências Diretas**: `FE-002, FE-019, FE-021, BE-022, DB-022`
- **Prioridade**: P0 | **Estimativa**: 5 SP | **Tipo**: feature
- **Objetivo**: Desenvolver a tela /aulas/:id/chamada otimizada para tablets e desktops permitindo lançar a presença de toda a turma com o mínimo de cliques.
- **Descrição**: Inicializar todos os alunos ativos como 'Presente' (PRESENT) por padrão, permitindo alternar em 1 clique para 'Falta' (ABSENT), 'Atraso' (LATE) ou 'Justificada' (JUSTIFIED com campo de observação). Incluir botão 'Marcar Todos Presentes', contador em tempo real de presentes/ausentes e botão 'Salvar Chamada' integrando com POST /api/v1/lessons/:id/attendance (BE-022).
- **História de Usuário**: Como Professor de Oficina, quero realizar a chamada da turma inteira em menos de 30 segundos, marcando apenas quem faltou.
- **Critérios de Aceitação**:
- Botões de status com alto contraste (Verde = Presente, Vermelho = Falta, Amarelo = Atraso, Azul = Justificado).
- Salva chamada em lote consumindo BE-022 com feedback visual Toast.
- Bloqueia edição caso a turma esteja encerrada (tratando erro 422 de BE-029).
- **Definição de Pronto (DoD)**: Interface de chamada rápida testada em desktop e mobile e sincronizada com BE-022.
- **Observações Técnicas**: Atende ao benefício esperado de tornar o registro mais rápido que planilhas convencionais.

---

### [FE-023] Implementar Indicador Visual de Presença/Faltas com Alerta de Limite 75%
- **ID**: `FE-023`
- **Título**: Implementar Indicador Visual de Presença/Faltas com Alerta de Limite 75%
- **Área**: Front-end
- **Epic**: EPIC-03: Diário de Classe: Notas & Frequência
- **Lote / Sprint**: Lote 3 (S3)
- **Sequência na Squad**: ⬅️ Anterior: `FE-022` | ➡️ Próximo: `FE-024`
- **Dependências Diretas**: `FE-002, FE-022, BE-023, DB-037`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Criar barra e badge termômetro de assiduidade que alerta visualmente quando o estudante se aproxima do limite mínimo legal de 75% de presença.
- **Descrição**: Desenvolver componente AttendanceGauge e tela /alunos/:id/frequencia consumindo GET /api/v1/students/:id/attendance (BE-023). Exibir cores semafóricas: Verde (>= 85%), Amarelo de Atenção (76% a 84%) e Vermelho Crítico (<= 75%), mostrando quantas horas-aula o aluno ainda pode faltar sem reprovar.
- **História de Usuário**: Como Aluno ou Professor, quero visualizar claramente a margem de faltas restante em cada módulo antes de atingir o limite crítico de 75%.
- **Critérios de Aceitação**:
- Exibe percentual exato, horas assistidas, horas faltadas e saldo de horas permitido.
- Destaca alerta visual preventivo quando frequência < 78%.
- Reutilizável tanto na visão do professor quanto no Portal do Aluno (FE-037).
- **Definição de Pronto (DoD)**: Componente e tela de frequência integrados a BE-023.
- **Observações Técnicas**: Acessível para daltônicos utilizando ícones + texto além das cores.

---

### [FE-024] Criar Painel de Cadastro e Listagem de Atividades Práticas de Oficina
- **ID**: `FE-024`
- **Título**: Criar Painel de Cadastro e Listagem de Atividades Práticas de Oficina
- **Área**: Front-end
- **Epic**: EPIC-04: Atividades Práticas de Oficina & Competências
- **Lote / Sprint**: Lote 3 (S3)
- **Sequência na Squad**: ⬅️ Anterior: `FE-023` | ➡️ Próximo: `FE-025`
- **Dependências Diretas**: `FE-004, FE-018, BE-015, BE-024, DB-023, DB-024`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Construir a rota /atividades-praticas para gestão das peças e exercícios de oficina agrupados por módulo SENAI.
- **Descrição**: Permitir ao professor visualizar e cadastrar atividades práticas (ex: 'Torneamento Cilíndrico Externo', 'Controle Dimensional com Micrômetro', 'Leitura de Desenho Técnico'), anexando link de folha de processo/desenho, prazo de entrega, pontuação máxima e rubricas vinculadas às competências do módulo (BE-024).
- **História de Usuário**: Como Instrutor SENAI, quero organizar as tarefas práticas de cada módulo com suas respectivas tolerâncias e competências.
- **Critérios de Aceitação**:
- Agrupamento visual por módulo de aprendizagem (learning_modules).
- Modal de criação dinâmico permitindo adicionar múltiplos critérios/rubricas (task_criteria).
- Exibe barra de progresso da turma (ex: '18/25 alunos concluíram esta peça').
- **Definição de Pronto (DoD)**: Tela /atividades-praticas funcional e integrada com BE-024.
- **Observações Técnicas**: Prepara o catálogo prático para avaliação rápida (FE-025) e rubricas (FE-026).

---

### [FE-025] Desenvolver Componente de Registro Rápido de Conclusão Prática pelo Docente
- **ID**: `FE-025`
- **Título**: Desenvolver Componente de Registro Rápido de Conclusão Prática pelo Docente
- **Área**: Front-end
- **Epic**: EPIC-04: Atividades Práticas de Oficina & Competências
- **Lote / Sprint**: Lote 3 (S3)
- **Sequência na Squad**: ⬅️ Anterior: `FE-024` | ➡️ Próximo: `FE-026`
- **Dependências Diretas**: `FE-005, FE-024, BE-025, DB-025`
- **Prioridade**: P0 | **Estimativa**: 5 SP | **Tipo**: feature
- **Objetivo**: Construir a tela /oficina/registro-rapido para o professor dar baixa e avaliar entregas práticas de bancada durante a aula na oficina.
- **Descrição**: Exibir matriz interativa (Alunos x Atividades Práticas do Módulo Ativo) com filtros rápidos ('Pendentes', 'Atrasadas', 'Concluídas'). Permitir registrar conclusão rápida ou abrir o modal de rubrica detalhada (FE-026), integrando com POST /api/v1/tasks/:id/evaluations (BE-025).
- **História de Usuário**: Como Professor de Oficina, quero registrar na hora que o aluno terminou a peça na máquina sem precisar sair da bancada para preencher planilhas.
- **Critérios de Aceitação**:
- Interface otimizada para toque (botões amplos para uso em tablet na oficina).
- Atualização otimista (optimistic UI) ao marcar atividade como avaliada.
- Sincroniza imediatamente com o painel de pendências do aluno (FE-036).
- **Definição de Pronto (DoD)**: Registro rápido de oficina funcional e integrado com BE-025.
- **Observações Técnicas**: Cumpre o requisito 4.1 (Registro rápido de conclusão de atividades práticas).

---

### [FE-026] Criar Modal de Avaliação por Rubricas de Habilidade Técnica (Tolerâncias/Acabamento)
- **ID**: `FE-026`
- **Título**: Criar Modal de Avaliação por Rubricas de Habilidade Técnica (Tolerâncias/Acabamento)
- **Área**: Front-end
- **Epic**: EPIC-04: Atividades Práticas de Oficina & Competências
- **Lote / Sprint**: Lote 3 (S3)
- **Sequência na Squad**: ⬅️ Anterior: `FE-025` | ➡️ Próximo: `FE-027`
- **Dependências Diretas**: `FE-004, FE-025, BE-025, DB-024, DB-026`
- **Prioridade**: P1 | **Estimativa**: 5 SP | **Tipo**: feature
- **Objetivo**: Disponibilizar modal para o professor atribuir nível de domínio (1 a 5) em cada critério técnico da atividade prática e registrar feedback.
- **Descrição**: Renderizar os critérios da tarefa (task_criteria) com seletores de nível 1 (Iniciante) a 5 (Avançado), calculando na tela a prévia da nota ponderada e enviando ao servidor (BE-025) para gravação oficial e geração de evidência de competência (skill_evidences).
- **História de Usuário**: Como Professor, quero avaliar cada critério técnico da peça (precisão dimensional, acabamento superficial, segurança) com rapidez e transparência.
- **Critérios de Aceitação**:
- Exibe descrição clara de cada rubrica e competência técnica associada.
- Campo de feedback técnico opcional por entrega.
- Calcula prévia visual da nota mantendo o cálculo definitivo validado pelo servidor.
- **Definição de Pronto (DoD)**: Modal de rubricas integrado ao fluxo de oficina (FE-025) e testado.
- **Observações Técnicas**: As notas lançadas aqui alimentam o gráfico radar do aluno (FE-038) e o diagnóstico (FE-042).

---

### [FE-027] Desenvolver Tela de Lançamento de Notas de Avaliações e Provas
- **ID**: `FE-027`
- **Título**: Desenvolver Tela de Lançamento de Notas de Avaliações e Provas
- **Área**: Front-end
- **Epic**: EPIC-03: Diário de Classe: Notas & Frequência
- **Lote / Sprint**: Lote 3 (S3)
- **Sequência na Squad**: ⬅️ Anterior: `FE-026` | ➡️ Próximo: `FE-028`
- **Dependências Diretas**: `FE-003, FE-005, BE-027, DB-027, DB-028`
- **Prioridade**: P0 | **Estimativa**: 5 SP | **Tipo**: feature
- **Objetivo**: Construir a tela /avaliacoes/notas em formato de grade editável (spreadsheet-like) com navegação por teclado (Tab/Enter/Setas).
- **Descrição**: Permitir ao professor criar avaliações formativas/microavaliações e digitar notas (0,00 a 10,00) e notas de recuperação para os alunos da turma. Destaca em vermelho notas abaixo da média de aprovação (6,00) e salva em lote via POST /api/v1/assessments/:id/grades (BE-027).
- **História de Usuário**: Como Professor, quero digitar as notas das provas usando apenas o teclado numérico e Enter, salvando toda a pauta de uma vez.
- **Critérios de Aceitação**:
- Validação instantânea impedindo valores < 0 ou > 10.
- Navegação fluida com Enter/Setas entre células da coluna de notas.
- Indicador visual de alterações não salvas (dirty state warning).
- **Definição de Pronto (DoD)**: Grade de lançamento de notas funcional e integrada com BE-027.
- **Observações Técnicas**: Desbloqueia o visualizador de médias consolidadas (FE-028).

---

### [FE-028] Criar Visualizador de Médias e Histórico Parcial por Aluno e Turma
- **ID**: `FE-028`
- **Título**: Criar Visualizador de Médias e Histórico Parcial por Aluno e Turma
- **Área**: Front-end
- **Epic**: EPIC-03: Diário de Classe: Notas & Frequência
- **Lote / Sprint**: Lote 3 (S3)
- **Sequência na Squad**: ⬅️ Anterior: `FE-027` | ➡️ Próximo: `FE-029`
- **Dependências Diretas**: `FE-005, FE-027, BE-028, DB-028`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Implementar a rota /turmas/:id/notas exibindo o quadro geral de médias ponderadas (provas + oficinas práticas) e situação de cada estudante.
- **Descrição**: Consumir GET /api/v1/classes/:id/grades-summary e POST /api/v1/classes/:id/calculate-averages (BE-028). Exibir colunas por módulo prático, média parcial, frequência acumulada e badge de situação ('Aprovado Parcial', 'Em Recuperação', 'Atenção Pedagógica').
- **História de Usuário**: Como Professor ou Coordenador, quero visualizar o quadro consolidado de notas e médias de todos os módulos da turma.
- **Critérios de Aceitação**:
- Botão 'Recalcular Médias' acionando BE-028 e atualizando a tabela.
- Destaque visual imediato para alunos abaixo da nota de corte do módulo.
- Clique no nome do aluno leva diretamente para a Visão 360° (FE-034).
- **Definição de Pronto (DoD)**: Tela /turmas/:id/notas implementada e validada com dados do seed.
- **Observações Técnicas**: Base direta para o Dashboard do Professor (FE-031).

---

### [FE-029] Implementar Filtros Avançados por Disciplina, Módulo e Período nas Tabelas
- **ID**: `FE-029`
- **Título**: Implementar Filtros Avançados por Disciplina, Módulo e Período nas Tabelas
- **Área**: Front-end
- **Epic**: EPIC-03: Diário de Classe: Notas & Frequência
- **Lote / Sprint**: Lote 3 (S3)
- **Sequência na Squad**: ⬅️ Anterior: `FE-028` | ➡️ Próximo: `FE-030`
- **Dependências Diretas**: `FE-003, FE-005, FE-009`
- **Prioridade**: P1 | **Estimativa**: 2 SP | **Tipo**: feature
- **Objetivo**: Criar barra de filtros globais reutilizável e sincronizada com a URL (Query Params) para filtrar turmas, disciplinas, módulos e status.
- **Descrição**: Desenvolver componente AcademicFilterBar em src/components/filters que sincroniza seleções (classId, subjectId, moduleId, search, status) com useSearchParams do React Router DOM, permitindo compartilhar links filtrados e preservar filtros ao navegar.
- **História de Usuário**: Como Professor, quero filtrar rapidamente por módulo prático (ex: 'Tornearia') e manter esse filtro ativo enquanto alterno entre chamada, tarefas e notas.
- **Critérios de Aceitação**:
- Sincroniza filtros selecionados na query string da URL (?classId=...&moduleId=...).
- Botão 'Limpar Filtros' restaurando o estado inicial.
- Integrado nas telas FE-021, FE-024, FE-027 e FE-028.
- **Definição de Pronto (DoD)**: Componente de filtro reutilizável integrado às telas do Lote 3 e Lote 4.
- **Observações Técnicas**: Usa debounce de 300ms no campo de busca textual para evitar chamadas excessivas à API.

---

### [FE-030] Testes Unitários de Componentes de Lançamento de Notas e Frequência
- **ID**: `FE-030`
- **Título**: Testes Unitários de Componentes de Lançamento de Notas e Frequência
- **Área**: Front-end
- **Epic**: EPIC-03: Diário de Classe: Notas & Frequência
- **Lote / Sprint**: Lote 3 (S3)
- **Sequência na Squad**: ⬅️ Anterior: `FE-029` | ➡️ Próximo: `FE-031`
- **Dependências Diretas**: `FE-021, FE-022, FE-023, FE-024, FE-025, FE-026, FE-027, FE-028, FE-029, BE-030`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: teste
- **Objetivo**: Garantir qualidade e ausência de regressões nos componentes críticos de chamada, rubricas e lançamento de notas do Lote 3.
- **Descrição**: Configurar Vitest + React Testing Library e escrever testes automatizados para: alternância de presença em 1 clique (FE-022), cálculo visual do indicador de 75% (FE-023), validação de limites 0-10 no input de notas (FE-027) e filtros de URL (FE-029).
- **História de Usuário**: Como Tech Lead Front-end, quero testes automatizados garantindo que o professor jamais perca dados ao lançar notas ou chamadas.
- **Critérios de Aceitação**:
- Comando npm run test executa todos os testes unitários do Lote 3 com sucesso.
- Cobertura dos cenários de erro da API (ex: turma encerrada 422).
- Zero warnings de acessibilidade básica nos formulários testados.
- **Definição de Pronto (DoD)**: Suíte de testes unitários do Lote 3 passando 100%.
- **Observações Técnicas**: Fecha o ciclo de Front-end do Lote 3 (Sprint S3).

---

### [FE-031] Desenvolver Dashboard do Professor: Visão Geral e Indicadores-Chave (KPIs)
- **ID**: `FE-031`
- **Título**: Desenvolver Dashboard do Professor: Visão Geral e Indicadores-Chave (KPIs)
- **Área**: Front-end
- **Epic**: EPIC-05: Dashboard Híbrido do Professor & Visão 360°
- **Lote / Sprint**: Lote 4 (S4)
- **Sequência na Squad**: ⬅️ Anterior: `FE-030` | ➡️ Próximo: `FE-032`
- **Dependências Diretas**: `FE-006, FE-028, FE-029, BE-031, DB-036`
- **Prioridade**: P0 | **Estimativa**: 5 SP | **Tipo**: feature
- **Objetivo**: Construir a tela principal do docente (/professor/dashboard) consolidando indicadores de desempenho, frequência, entregas práticas e alertas de risco.
- **Descrição**: Consumir GET /api/v1/dashboard/teacher/classes/:id (BE-031). Exibir 4 KPI Cards no topo (Média da Turma, Assiduidade Geral, % de Peças Práticas Entregues, Alunos em Atenção Pedagógica), visão modular (Desenho Técnico, Metrologia, Tornearia) e lista prioritária de acompanhamento.
- **História de Usuário**: Como Professor SENAI, quero um dashboard híbrido que una notas, frequência, oficinas e alertas em uma única tela para apoiar decisões pedagógicas.
- **Critérios de Aceitação**:
- Carrega indicadores reais da API BE-031 com Skeleton Loading suave.
- Permite alternar entre turmas e módulos pelo filtro superior.
- Atalhos rápidos para 'Iniciar Chamada' (FE-022) e 'Avaliar Oficina' (FE-025).
- **Definição de Pronto (DoD)**: Dashboard híbrido do professor funcional, responsivo e integrado com BE-031.
- **Observações Técnicas**: Coração do requisito 4.1 (Dashboard híbrido para professores).

---

### [FE-032] Criar Card de Aluno em Risco Acadêmico com Motivo Explicável e Ação Rápida
- **ID**: `FE-032`
- **Título**: Criar Card de Aluno em Risco Acadêmico com Motivo Explicável e Ação Rápida
- **Área**: Front-end
- **Epic**: EPIC-05: Dashboard Híbrido do Professor & Visão 360°
- **Lote / Sprint**: Lote 4 (S4)
- **Sequência na Squad**: ⬅️ Anterior: `FE-031` | ➡️ Próximo: `FE-033`
- **Dependências Diretas**: `FE-004, FE-031, BE-032, BE-033, BE-039, DB-034`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Desenvolver componente visual que apresenta os alertas de risco acadêmico de forma transparente, ética e explicável para o professor.
- **Descrição**: Consumir GET /api/v1/dashboard/teacher/at-risk (BE-033) e PATCH /api/v1/alerts/:id/resolve (BE-039). Exibir badge de nível de atenção, texto explicativo das evidências (explainable_reason), métricas atuais e botões de ação: 'Ver Ficha 360°', 'Registrar Intervenção' e 'Marcar Acompanhado'.
- **História de Usuário**: Como Professor, quero entender exatamente por que um estudante entrou em alerta de atenção e registrar a intervenção pedagógica realizada.
- **Critérios de Aceitação**:
- Exibe claramente a regra e os dados que geraram o alerta (ex: frequência 74% + 2 práticas pendentes).
- Inclui nota ética: indicador de apoio pedagógico, não decisão automática.
- Modal rápido para resolver/acompanhar o alerta integrando com BE-039.
- **Definição de Pronto (DoD)**: Componente de alertas explicáveis integrado ao Dashboard do Professor.
- **Observações Técnicas**: Conecta-se também ao modal de observações pedagógicas restritas (FE-046).

---

### [FE-033] Criar Gráfico de Evolução de Habilidades e Desempenho da Turma
- **ID**: `FE-033`
- **Título**: Criar Gráfico de Evolução de Habilidades e Desempenho da Turma
- **Área**: Front-end
- **Epic**: EPIC-05: Dashboard Híbrido do Professor & Visão 360°
- **Lote / Sprint**: Lote 4 (S4)
- **Sequência na Squad**: ⬅️ Anterior: `FE-032` | ➡️ Próximo: `FE-034`
- **Dependências Diretas**: `FE-001, FE-031, BE-031, DB-036`
- **Prioridade**: P1 | **Estimativa**: 5 SP | **Tipo**: feature
- **Objetivo**: Implementar gráficos analíticos interativos mostrando a evolução das médias, assiduidade e domínio de competências da turma entre os módulos.
- **Descrição**: Criar componentes visuais de gráfico de barras e linhas (SVG nativo otimizado ou Recharts) no Dashboard do Professor comparando o rendimento entre os módulos práticos (ex: Desenho Técnico vs Metrologia vs Tornearia) e a distribuição de notas da turma.
- **História de Usuário**: Como Professor ou Coordenador, quero visualizar graficamente em qual módulo prático a turma está encontrando maior dificuldade coletiva.
- **Critérios de Aceitação**:
- Tooltips informativos ao passar o mouse exibindo média, mediana e taxa de conclusão.
- Legendas acessíveis e cores alinhadas ao Design System SENAI (FE-001).
- Responsivo em diferentes resoluções de tela.
- **Definição de Pronto (DoD)**: Gráficos de evolução da turma integrados ao Dashboard do Professor.
- **Observações Técnicas**: Ajuda a coordenação a identificar gargalos em módulos ou equipamentos de oficina.

---

### [FE-034] Desenvolver Visão 360° do Aluno (Ficha Completa: Notas, Faltas e Habilidades)
- **ID**: `FE-034`
- **Título**: Desenvolver Visão 360° do Aluno (Ficha Completa: Notas, Faltas e Habilidades)
- **Área**: Front-end
- **Epic**: EPIC-05: Dashboard Híbrido do Professor & Visão 360°
- **Lote / Sprint**: Lote 4 (S4)
- **Sequência na Squad**: ⬅️ Anterior: `FE-033` | ➡️ Próximo: `FE-035`
- **Dependências Diretas**: `FE-009, FE-023, FE-031, FE-032, BE-031, DB-036`
- **Prioridade**: P0 | **Estimativa**: 5 SP | **Tipo**: feature
- **Objetivo**: Construir a tela /professor/alunos/:id reunindo todo o histórico, desempenho por disciplina, rubricas de oficina, autoavaliações e intervenções de um estudante.
- **Descrição**: Consumir GET /api/v1/students/:id/360 (BE-031). Apresentar cabeçalho com perfil do estudante, termômetro de presença (FE-023), gráfico radar de competências (FE-038), histórico de entregas práticas, comparativo de autoavaliação (FE-042), alertas e aba exclusiva de Observações Pedagógicas Restritas (FE-046).
- **História de Usuário**: Como Professor ou Coordenador, quero acessar uma ficha 360° consolidada de um estudante em todas as disciplinas para embasar reuniões de orientação.
- **Critérios de Aceitação**:
- Reúne visão multidisciplinar (todas as matérias e módulos do aluno na turma).
- Abas organizadas: Desempenho & Oficinas, Competências & Diagnóstico, Frequência e Observações Pedagógicas.
- Protegida por RoleRoute apenas para TEACHER, COORDINATOR e ADMIN.
- **Definição de Pronto (DoD)**: Ficha 360° do aluno completa e integrada aos endpoints do Lote 4.
- **Observações Técnicas**: Atende ao primeiro item do requisito 4.1 (Visão geral do aluno em todas as disciplinas).

---

### [FE-035] Desenvolver Portal de Autonomia do Aluno (Visão Inicial do Estudante)
- **ID**: `FE-035`
- **Título**: Desenvolver Portal de Autonomia do Aluno (Visão Inicial do Estudante)
- **Área**: Front-end
- **Epic**: EPIC-06: Portal de Autonomia do Aluno & Pendências
- **Lote / Sprint**: Lote 4 (S4)
- **Sequência na Squad**: ⬅️ Anterior: `FE-034` | ➡️ Próximo: `FE-036`
- **Dependências Diretas**: `FE-008, FE-012, BE-034, DB-036`
- **Prioridade**: P0 | **Estimativa**: 5 SP | **Tipo**: feature
- **Objetivo**: Construir o painel privado inicial do estudante (/aluno/painel) promovendo autonomia no acompanhamento de seu progresso acadêmico.
- **Descrição**: Consumir GET /api/v1/dashboard/student/me (BE-034). Exibir saudação personalizada, cards de progresso nos módulos atuais, resumo de assiduidade, alerta amigável de próximas entregas práticas, atalho para Autoavaliação (FE-041) e botão de destaque 'Preciso de Ajuda / Mentoria' (FE-044).
- **História de Usuário**: Como Estudante SENAI, quero um portal claro e motivador onde eu consulte meu progresso geral, próximas entregas e peça apoio sempre que precisar.
- **Critérios de Aceitação**:
- Exibe exclusivamente os dados do próprio aluno logado.
- Cards de progresso por módulo com percentual concluído.
- Links diretos para Pendências (FE-036), Notas (FE-037), Competências (FE-038) e Solicitar Ajuda (FE-044).
- **Definição de Pronto (DoD)**: Portal inicial do aluno implementado e integrado com BE-034.
- **Observações Técnicas**: Cumpre o requisito 4.2 (Portal de autonomia do aluno).

---

### [FE-036] Criar Painel de Tarefas Pendentes, Concluídas e Atrasadas do Estudante
- **ID**: `FE-036`
- **Título**: Criar Painel de Tarefas Pendentes, Concluídas e Atrasadas do Estudante
- **Área**: Front-end
- **Epic**: EPIC-06: Portal de Autonomia do Aluno & Pendências
- **Lote / Sprint**: Lote 4 (S4)
- **Sequência na Squad**: ⬅️ Anterior: `FE-035` | ➡️ Próximo: `FE-037`
- **Dependências Diretas**: `FE-006, FE-026, FE-035, BE-026, DB-025`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Desenvolver a rota /aluno/pendencias organizando todas as atividades práticas e teóricas do estudante por status e prazo.
- **Descrição**: Consumir GET /api/v1/students/:id/pending-tasks (BE-026). Dividir em 3 abas ou colunas claras: 'Atrasadas' (destaque prioritário), 'Pendentes / Próximas' e 'Concluídas / Avaliadas' (exibindo a nota e o feedback técnico dado pelo professor nas rubricas).
- **História de Usuário**: Como Estudante, quero saber exatamente quais peças e atividades estão pendentes ou atrasadas e ler o feedback técnico do professor nas que já entreguei.
- **Critérios de Aceitação**:
- Destaca prazos próximos ou vencidos com badges semafóricos.
- Ao clicar em uma atividade avaliada, exibe o detalhamento das rubricas (FE-026) e comentários do docente.
- Estado vazio comemorativo ('Parabéns! Nenhuma pendência em atraso').
- **Definição de Pronto (DoD)**: Painel de pendências do aluno funcional e sincronizado com BE-026.
- **Observações Técnicas**: Conecta o registro rápido do professor na oficina (FE-025) diretamente à visão do aluno.

---

### [FE-037] Desenvolver Visualização de Notas e Frequência do Próprio Aluno
- **ID**: `FE-037`
- **Título**: Desenvolver Visualização de Notas e Frequência do Próprio Aluno
- **Área**: Front-end
- **Epic**: EPIC-06: Portal de Autonomia do Aluno & Pendências
- **Lote / Sprint**: Lote 4 (S4)
- **Sequência na Squad**: ⬅️ Anterior: `FE-036` | ➡️ Próximo: `FE-038`
- **Dependências Diretas**: `FE-023, FE-035, BE-023, BE-034, DB-028, DB-037`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Construir a tela /aluno/desempenho para consulta detalhada do boletim modular e extrato de presença do estudante.
- **Descrição**: Combinar dados de BE-023 e BE-034 exibindo acordeão por disciplina técnica e seus módulos de aprendizagem: notas de provas, notas de oficinas práticas, média parcial do módulo e o componente AttendanceGauge (FE-023) de controle do limite de 75% de presença.
- **História de Usuário**: Como Estudante, quero acompanhar minhas notas de cada módulo e minha frequência atualizada sem precisar esperar o final do semestre.
- **Critérios de Aceitação**:
- Exibe memória de cálculo transparente de como a média de cada módulo é composta.
- Mostra histórico de faltas por data de aula.
- Layout limpo e adaptável para consulta pelo celular.
- **Definição de Pronto (DoD)**: Tela de boletim e frequência do aluno implementada e testada.
- **Observações Técnicas**: Promove transparência acadêmica e evita surpresas de reprovação por falta.

---

### [FE-038] Criar Gráfico Radar de Competências Técnicas do Aluno (Ex: Tornearia, Fresamento)
- **ID**: `FE-038`
- **Título**: Criar Gráfico Radar de Competências Técnicas do Aluno (Ex: Tornearia, Fresamento)
- **Área**: Front-end
- **Epic**: EPIC-06: Portal de Autonomia do Aluno & Pendências
- **Lote / Sprint**: Lote 4 (S4)
- **Sequência na Squad**: ⬅️ Anterior: `FE-037` | ➡️ Próximo: `FE-039`
- **Dependências Diretas**: `FE-034, FE-035, BE-034, BE-038, DB-015, DB-033`
- **Prioridade**: P1 | **Estimativa**: 5 SP | **Tipo**: feature
- **Objetivo**: Implementar visualização gráfica em formato Radar (Spider Chart) e barras de proficiência para a rota /aluno/competencias e Ficha 360° (FE-034).
- **Descrição**: Renderizar o domínio do estudante (escala 1 a 5) nas competências técnicas do curso (ex: Leitura de Desenho Técnico, Medição com Paquímetro/Micrômetro, Operação de Torno, Segurança NR-12), baseando-se nas evidências avaliadas pelo professor (skill_evidences).
- **História de Usuário**: Como Estudante, quero visualizar um mapa gráfico das minhas habilidades técnicas para saber em quais competências já sou proficiente e quais preciso praticar mais.
- **Critérios de Aceitação**:
- Gráfico Radar SVG responsivo comparando 'Nível Atual Verificado' vs 'Meta do Módulo'.
- Lista complementar em cards acessíveis para leitores de tela.
- Reutilizado também na Ficha 360° do Professor (FE-034).
- **Definição de Pronto (DoD)**: Gráfico radar de competências implementado e integrado ao Portal do Aluno e Visão 360°.
- **Observações Técnicas**: Prepara a sobreposição visual com a autoavaliação em FE-042.

---

### [FE-039] Desenvolver Linha do Tempo de Conquistas e Marcos Acadêmicos
- **ID**: `FE-039`
- **Título**: Desenvolver Linha do Tempo de Conquistas e Marcos Acadêmicos
- **Área**: Front-end
- **Epic**: EPIC-06: Portal de Autonomia do Aluno & Pendências
- **Lote / Sprint**: Lote 4 (S4)
- **Sequência na Squad**: ⬅️ Anterior: `FE-038` | ➡️ Próximo: `FE-040`
- **Dependências Diretas**: `FE-035, BE-034, DB-039`
- **Prioridade**: P2 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Construir a rota /aluno/trajetoria exibindo cronologicamente os módulos concluídos e a evolução histórica do estudante.
- **Descrição**: Consumir os registros de student_milestone_history vindos de BE-034 e renderizar uma timeline vertical interativa destacando módulos superados, subidas de nível técnico e metas alcançadas ao longo do semestre.
- **História de Usuário**: Como Estudante, quero enxergar minha linha do tempo de evolução desde o primeiro dia de aula até o módulo atual.
- **Critérios de Aceitação**:
- Timeline vertical com ícones distintos por tipo de marco (Módulo Concluído, Evolução de Habilidade, Assiduidade).
- Exibe datas formatadas em pt-BR e descrição motivadora.
- Integrada com as conquistas de gamificação (FE-047).
- **Definição de Pronto (DoD)**: Linha do tempo acadêmica implementada e funcional.
- **Observações Técnicas**: Atende ao requisito de visualização do histórico de evolução acadêmica.

---

### [FE-040] Implementar Responsividade Mobile do Dashboard e Portal do Aluno
- **ID**: `FE-040`
- **Título**: Implementar Responsividade Mobile do Dashboard e Portal do Aluno
- **Área**: Front-end
- **Epic**: EPIC-06: Portal de Autonomia do Aluno & Pendências
- **Lote / Sprint**: Lote 4 (S4)
- **Sequência na Squad**: ⬅️ Anterior: `FE-039` | ➡️ Próximo: `FE-041`
- **Dependências Diretas**: `FE-007, FE-008, FE-031, FE-034, FE-035, FE-036, FE-037, FE-038`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: melhoria
- **Objetivo**: Garantir que todas as telas do Dashboard do Professor e do Portal do Aluno funcionem perfeitamente em smartphones (360px+) e tablets de oficina.
- **Descrição**: Revisar e ajustar breakpoints Tailwind v4 (sm, md, lg, xl), transformar tabelas densas em cards empilhados em telas mobile, ajustar menu inferior/drawer (FE-008) e validar áreas de toque mínimas de 44x44px para uso em bancada.
- **História de Usuário**: Como Aluno no celular ou Professor com tablet na oficina, quero usar todas as funções do sistema sem cortes de layout ou botões minúsculos.
- **Critérios de Aceitação**:
- Zero barra de rolagem horizontal indesejada em viewports de 360px a 1920px.
- Gráficos (FE-033 e FE-038) redimensionam proporcionalmente em telas pequenas.
- Validado em perfis mobile (iPhone SE, Android médio, iPad).
- **Definição de Pronto (DoD)**: Todas as telas até o Lote 4 100% responsivas em mobile e tablet.
- **Observações Técnicas**: Fecha o ciclo de Front-end do Lote 4 (Sprint S4).

---

### [FE-041] Desenvolver Interface de Autoavaliação de Domínio de Habilidades Práticas
- **ID**: `FE-041`
- **Título**: Desenvolver Interface de Autoavaliação de Domínio de Habilidades Práticas
- **Área**: Front-end
- **Epic**: EPIC-07: Autoavaliação & Motor de Diagnóstico Explicável
- **Lote / Sprint**: Lote 5 (S5)
- **Sequência na Squad**: ⬅️ Anterior: `FE-040` | ➡️ Próximo: `FE-042`
- **Dependências Diretas**: `FE-003, FE-035, BE-035, BE-036, DB-031, DB-032`
- **Prioridade**: P1 | **Estimativa**: 5 SP | **Tipo**: feature
- **Objetivo**: Construir a tela /aluno/autoavaliacao para o estudante avaliar seu próprio domínio nas competências práticas do módulo.
- **Descrição**: Consumir GET /api/v1/classes/:classId/self-assessments/forms (BE-035) e enviar respostas para POST /api/v1/self-assessments/submit (BE-036). Apresentar formulário passo a passo com escala clara de 1 a 5 para cada competência técnica, grau de confiança na operação da máquina e campo para relatar dificuldades específicas.
- **História de Usuário**: Como Estudante, quero realizar minha autoavaliação das habilidades práticas do plano de ensino para refletir sobre meu aprendizado e sinalizar onde tenho dúvidas.
- **Critérios de Aceitação**:
- Exibe descrição didática do que significa cada nível (1 a 5) naquela competência.
- Impede envio incompleto com validação visual amigável (FE-003).
- Após envio, redireciona para o comparativo explicável (FE-042) ou sugere pedir mentoria (FE-044).
- **Definição de Pronto (DoD)**: Fluxo de autoavaliação do estudante implementado e integrado com BE-035 e BE-036.
- **Observações Técnicas**: Atende ao requisito 4.3 (Autoavaliação das habilidades práticas conforme o plano de ensino).

---

### [FE-042] Criar Componente Comparativo Visual: Autoavaliação vs Avaliação do Professor
- **ID**: `FE-042`
- **Título**: Criar Componente Comparativo Visual: Autoavaliação vs Avaliação do Professor
- **Área**: Front-end
- **Epic**: EPIC-07: Autoavaliação & Motor de Diagnóstico Explicável
- **Lote / Sprint**: Lote 5 (S5)
- **Sequência na Squad**: ⬅️ Anterior: `FE-041` | ➡️ Próximo: `FE-043`
- **Dependências Diretas**: `FE-034, FE-038, FE-041, BE-037, BE-038, DB-035, DB-038`
- **Prioridade**: P1 | **Estimativa**: 5 SP | **Tipo**: feature
- **Objetivo**: Exibir lado a lado a percepção do aluno e a avaliação prática verificada pelo professor, apresentando diagnósticos explicáveis, evidências e limitações.
- **Descrição**: Consumir GET /api/v1/diagnostics/discrepancies (BE-038). Renderizar barras duplas comparativas (Percepção do Aluno vs Evidência Prática Docente) por competência, destacando divergências relevantes e exibindo a caixa de Diagnóstico Explicável (critérios utilizados, entregas avaliadas e limitações do diagnóstico).
- **História de Usuário**: Como Professor ou Estudante, quero comparar a autoavaliação com os resultados práticos reais das oficinas para alinhar expectativas e direcionar mentorias.
- **Critérios de Aceitação**:
- Exibe aviso claro de que a autoavaliação é uma ferramenta formativa e não substitui a avaliação prática.
- Mostra as evidências concretas (peças/rubricas) que compõem a nota do professor.
- Permite ao professor converter uma divergência em convite de mentoria ou alerta acompanhado.
- **Definição de Pronto (DoD)**: Componente comparativo e de diagnóstico explicável integrado à visão do professor e do aluno.
- **Observações Técnicas**: Entrega completa da seção 4.3 (Autoavaliação e diagnóstico explicável sem rótulos permanentes).

---

### [FE-043] Desenvolver Mural de Avisos da Turma com Filtro por Disciplina
- **ID**: `FE-043`
- **Título**: Desenvolver Mural de Avisos da Turma com Filtro por Disciplina
- **Área**: Front-end
- **Epic**: EPIC-08: Comunicação Oficial & Solicitações Confidenciais
- **Lote / Sprint**: Lote 5 (S5)
- **Sequência na Squad**: ⬅️ Anterior: `FE-042` | ➡️ Próximo: `FE-044`
- **Dependências Diretas**: `FE-002, FE-004, FE-029, BE-041, BE-042, DB-041`
- **Prioridade**: P1 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Construir a rota /mural para visualização e publicação de comunicados oficiais da turma e das oficinas.
- **Descrição**: Consumir GET /api/v1/announcements (BE-042) e POST /api/v1/announcements (BE-041). Exibir avisos fixados no topo (pinned), tags de prioridade ('Urgente', 'Importante', 'Informativo'), filtro por disciplina e botão 'Novo Comunicado' visível apenas para professores e coordenadores.
- **História de Usuário**: Como Aluno ou Professor, quero um mural oficial centralizado para acompanhar avisos importantes de cada matéria e oficina.
- **Critérios de Aceitação**:
- Avisos fixados aparecem destacados no topo com ícone Pin.
- Oculta botões de criação/exclusão para usuários com perfil STUDENT.
- Filtragem instantânea por disciplina e busca por palavra-chave.
- **Definição de Pronto (DoD)**: Mural de avisos implementado e integrado com BE-041 e BE-042.
- **Observações Técnicas**: Atende ao requisito 4.4 (Mural de avisos da turma).

---

### [FE-044] Criar Interface para Aluno Solicitar Ajuda Pedagógica Confidencial
- **ID**: `FE-044`
- **Título**: Criar Interface para Aluno Solicitar Ajuda Pedagógica Confidencial
- **Área**: Front-end
- **Epic**: EPIC-08: Comunicação Oficial & Solicitações Confidenciais
- **Lote / Sprint**: Lote 5 (S5)
- **Sequência na Squad**: ⬅️ Anterior: `FE-043` | ➡️ Próximo: `FE-045`
- **Dependências Diretas**: `FE-003, FE-035, BE-043, BE-044, DB-042, DB-044`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Construir a rota /ajuda/solicitar permitindo ao estudante abrir chamados de apoio/mentoria confidenciais e trocar mensagens com o professor.
- **Descrição**: Consumir POST /api/v1/help-requests e GET /api/v1/help-requests (BE-043, BE-044). Incluir seleção de disciplina/módulo prático, tipo de dificuldade, descrição, toggle 'Pedido Confidencial (visível apenas para o professor e coordenação)' marcado por padrão e chat interno com status ('Aberto', 'Em Atendimento', 'Resolvido').
- **História de Usuário**: Como Estudante, quero pedir ajuda ao professor quando não entender uma operação de máquina ou matéria, com total garantia de que outros alunos não verão meu pedido.
- **Critérios de Aceitação**:
- Exibe selo de segurança informando que o pedido é privado e confidencial.
- Lista o histórico de solicitações do próprio aluno com status de leitura e resposta.
- Chat interno funcional consumindo POST /api/v1/help-requests/:id/messages (BE-044).
- **Definição de Pronto (DoD)**: Tela de solicitação de ajuda confidencial do aluno funcional e testada.
- **Observações Técnicas**: Cumpre o requisito de privacidade e canal de ajuda do estudante (seção 4.4).

---

### [FE-045] Criar Painel do Professor para Gerenciar e Responder Pedidos de Ajuda
- **ID**: `FE-045`
- **Título**: Criar Painel do Professor para Gerenciar e Responder Pedidos de Ajuda
- **Área**: Front-end
- **Epic**: EPIC-08: Comunicação Oficial & Solicitações Confidenciais
- **Lote / Sprint**: Lote 5 (S5)
- **Sequência na Squad**: ⬅️ Anterior: `FE-044` | ➡️ Próximo: `FE-046`
- **Dependências Diretas**: `FE-007, FE-034, FE-044, BE-043, BE-044, DB-042, DB-044`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Desenvolver a rota /professor/solicitacoes para os docentes atenderem, responderem e encerrarem solicitações de ajuda e mentoria dos alunos.
- **Descrição**: Consumir GET /api/v1/help-requests e PATCH /api/v1/help-requests/:id (BE-043, BE-044). Apresentar fila de chamados filtrável por status ('Novos', 'Em Atendimento', 'Concluídos') e módulo, chat de resposta direta ao aluno e botão para encerrar com resumo da orientação prestada.
- **História de Usuário**: Como Professor, quero visualizar todos os pedidos de ajuda dos meus alunos em uma caixa organizada para responder dúvidas e agendar mentorias.
- **Critérios de Aceitação**:
- Atualiza contador de solicitações não lidas no Header (FE-007).
- Permite alterar status para 'Em Atendimento' e 'Resolvido' com resumo final.
- Atalho direto para abrir a Ficha 360° do aluno solicitante (FE-034).
- **Definição de Pronto (DoD)**: Painel docente de atendimento de solicitações integrado com BE-044.
- **Observações Técnicas**: Fecha o ciclo de comunicação aluno-professor.

---

### [FE-046] Criar Interface Segura para Registro de Observações Pedagógicas Restritas
- **ID**: `FE-046`
- **Título**: Criar Interface Segura para Registro de Observações Pedagógicas Restritas
- **Área**: Front-end
- **Epic**: EPIC-08: Comunicação Oficial & Solicitações Confidenciais
- **Lote / Sprint**: Lote 5 (S5)
- **Sequência na Squad**: ⬅️ Anterior: `FE-045` | ➡️ Próximo: `FE-047`
- **Dependências Diretas**: `FE-004, FE-034, BE-045, DB-043`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Desenvolver componente e modal exclusivo para professores e coordenadores registrarem observações pedagógicas com controle de escopo de visibilidade.
- **Descrição**: Integrar na Ficha 360° (FE-034) consumindo POST /api/v1/pedagogical-notes e GET /api/v1/students/:id/pedagogical-notes (BE-045). Permitir selecionar categoria ('Intervenção', 'Mentoria', 'Acompanhamento') e visibilidade ('Apenas Eu', 'Professores da Turma e Coordenação', 'Apenas Coordenação').
- **História de Usuário**: Como Professor ou Coordenador, quero registrar observações pedagógicas de acompanhamento sabendo exatamente quem terá permissão para lê-las.
- **Critérios de Aceitação**:
- Componente jamais é renderizado ou importado nas rotas de perfil STUDENT.
- Exibe claramente o cadeado e o escopo de visibilidade de cada observação.
- Permite definir data de retorno/acompanhamento (followupDate).
- **Definição de Pronto (DoD)**: Interface de observações pedagógicas restritas integrada à Ficha 360° e validada.
- **Observações Técnicas**: Garante sigilo pedagógico em conformidade com a seção 4.4 e seção 14.

---

### [FE-047] Desenvolver Painel de Gamificação e Conquistas (Badges) do Aluno
- **ID**: `FE-047`
- **Título**: Desenvolver Painel de Gamificação e Conquistas (Badges) do Aluno
- **Área**: Front-end
- **Epic**: EPIC-09: Gamificação Pedagógica Transparente & Níveis
- **Lote / Sprint**: Lote 5 (S5)
- **Sequência na Squad**: ⬅️ Anterior: `FE-046` | ➡️ Próximo: `FE-048`
- **Dependências Diretas**: `FE-035, FE-039, BE-046, BE-047, DB-045, DB-046`
- **Prioridade**: P2 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Construir a rota /aluno/conquistas exibindo o nível de habilidade do estudante, barra de XP e insígnias desbloqueadas com regras transparentes.
- **Descrição**: Consumir GET /api/v1/gamification/badges (BE-046). Apresentar o nível atual (ex: 'Nível 3 — Praticante de Precisão'), galeria de insígnias conquistadas (coloridas) e bloqueadas (com explicação clara de como desbloquear cada uma no laboratório), sem exibir ranking vexatório entre estudantes.
- **História de Usuário**: Como Estudante, quero ver minhas insígnias técnicas e meu nível de evolução nas oficinas com regras claras e motivadoras.
- **Critérios de Aceitação**:
- Exibe explicação transparente da regra de pontuação de cada badge (criteria_explanation).
- Não expõe alunos com menor pontuação (proteção contra exposição indevida).
- Integrado aos cards de resumo do Portal do Aluno (FE-035).
- **Definição de Pronto (DoD)**: Tela de conquistas e gamificação implementada e integrada com BE-046.
- **Observações Técnicas**: Atende ao requisito 4.2 (Cards de progresso, níveis de habilidade e gamificação ética).

---

### [FE-048] Desenvolver Central de Exportação de Relatórios da Turma (PDF / CSV)
- **ID**: `FE-048`
- **Título**: Desenvolver Central de Exportação de Relatórios da Turma (PDF / CSV)
- **Área**: Front-end
- **Epic**: EPIC-10: Relatórios, Governança de Dados & Qualidade
- **Lote / Sprint**: Lote 5 (S5)
- **Sequência na Squad**: ⬅️ Anterior: `FE-047` | ➡️ Próximo: `FE-049`
- **Dependências Diretas**: `FE-005, FE-029, FE-031, BE-048, BE-049, DB-047`
- **Prioridade**: P1 | **Estimativa**: 3 SP | **Tipo**: feature
- **Objetivo**: Construir a rota /relatorios permitindo que professores e coordenadores filtrem, pré-visualizem e exportem relatórios gerenciais de desempenho e frequência.
- **Descrição**: Consumir GET /api/v1/reports/performance (BE-049) e GET /api/v1/admin/audit-logs (BE-048). Disponibilizar seleção de Turma, Disciplina, Módulo e Tipo de Relatório ('Desempenho Geral para Conselho de Classe', 'Mapa de Frequência', 'Relatório de Alertas e Intervenções'), com download em CSV e impressão formatada em PDF (@media print).
- **História de Usuário**: Como Coordenador ou Professor, quero gerar e baixar relatórios prontos da turma para reuniões pedagógicas e conselho de classe.
- **Critérios de Aceitação**:
- Download de arquivo CSV formatado corretamente ao clicar em 'Exportar CSV'.
- Folha de estilo de impressão (@media print) gerando relatório PDF limpo com cabeçalho institucional SENAI.
- Visualizador de logs de auditoria disponível para perfil ADMIN/COORDINATOR.
- **Definição de Pronto (DoD)**: Central de relatórios funcional e integrada com BE-048 e BE-049.
- **Observações Técnicas**: Atende ao requisito funcional de relatórios e exportação de dados.

---

### [FE-049] Implementar Tratamento de Acessibilidade (Atalhos de Teclado e Leitor de Tela)
- **ID**: `FE-049`
- **Título**: Implementar Tratamento de Acessibilidade (Atalhos de Teclado e Leitor de Tela)
- **Área**: Front-end
- **Epic**: EPIC-10: Relatórios, Governança de Dados & Qualidade
- **Lote / Sprint**: Lote 5 (S5)
- **Sequência na Squad**: ⬅️ Anterior: `FE-048` | ➡️ Próximo: `FE-050`
- **Dependências Diretas**: `FE-001, FE-003, FE-004, FE-022, FE-027, FE-040, FE-041`
- **Prioridade**: P1 | **Estimativa**: 3 SP | **Tipo**: melhoria
- **Objetivo**: Realizar auditoria e refinamento de acessibilidade WCAG 2.1 AA em todas as telas da aplicação.
- **Descrição**: Garantir navegação completa por teclado (Tab order lógico, Skip-to-content link, outline de foco visível), atributos ARIA em tabelas, gráficos e alertas, textos alternativos e contraste mínimo de 4.5:1 em todos os badges e botões.
- **História de Usuário**: Como Usuário com necessidades de acessibilidade, quero navegar por todas as telas do sistema usando teclado ou leitor de tela sem barreiras.
- **Critérios de Aceitação**:
- Pontuação de Acessibilidade >= 95 no Lighthouse nas rotas principais.
- Todos os gráficos possuem tabela/descrição acessível equivalente (sr-only).
- Navegação por teclado validada no login, chamada rápida, notas e autoavaliação.
- **Definição de Pronto (DoD)**: Auditoria de acessibilidade concluída e aprovada sem violações críticas.
- **Observações Técnicas**: Requisito obrigatório de qualidade e acessibilidade (seção 5 e seção 7).

---

### [FE-050] Implementar Suíte de Testes End-to-End (E2E) dos Fluxos Críticos com Playwright
- **ID**: `FE-050`
- **Título**: Implementar Suíte de Testes End-to-End (E2E) dos Fluxos Críticos com Playwright
- **Área**: Front-end
- **Epic**: EPIC-10: Relatórios, Governança de Dados & Qualidade
- **Lote / Sprint**: Lote 5 (S5)
- **Sequência na Squad**: ⬅️ Anterior: `FE-049` | ➡️ Próximo: `Marco Final Concluído (100%)`
- **Dependências Diretas**: `FE-001, FE-010, FE-020, FE-030, FE-040, FE-042, FE-045, FE-048, FE-049, BE-050, DB-050`
- **Prioridade**: P0 | **Estimativa**: 5 SP | **Tipo**: teste
- **Objetivo**: Validar a integração completa de ponta a ponta (Front-end + Back-end + Banco de Dados) cobrindo os fluxos essenciais do sistema para entrega final do semestre.
- **Descrição**: Configurar Playwright (ou Cypress) e automatizar os 5 fluxos de ponta a ponta: (1) Login e redirecionamento por RBAC; (2) Professor registra aula, faz chamada em 1 clique e avalia tarefa prática de oficina; (3) Sistema gera alerta explicável no Dashboard do Professor; (4) Aluno consulta Portal de Autonomia, envia Autoavaliação e visualiza comparativo; (5) Aluno abre pedido de ajuda confidencial e Professor responde.
- **História de Usuário**: Como Equipe do Projeto NEXA, queremos uma suíte E2E que comprove que os 50 cards de Front, 50 de Back e 50 de Banco funcionam integrados perfeitamente.
- **Critérios de Aceitação**:
- Todos os 5 fluxos críticos E2E passando de ponta a ponta conectando FE + BE + DB.
- Verifica isolamento de segurança (Aluno não acessa rotas ou dados de outros estudantes).
- Gera evidências automatizadas (screenshots/vídeo) para DOC-016, DOC-019 e DOC-020.
- **Definição de Pronto (DoD)**: Aplicação 100% integrada, testada ponta a ponta e pronta para apresentação final da banca SENAI.
- **Observações Técnicas**: Marco de encerramento (Card 50/50) da squad de Front-end, unificando DB-050, BE-050 e DOC-020.

