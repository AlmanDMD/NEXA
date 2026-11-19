# Front-end — NEXA (Monitoramento Acadêmico SENAI)

Interface web da plataforma **NEXA**, desenvolvida para centralizar o acompanhamento pedagógico, a frequência regimental (**limite mínimo de 75% do SENAI**), as atividades práticas de oficina e a evolução dos estudantes nas visões de **Professor** e **Aluno**.

---

## Tecnologias Utilizadas

- **React 19** (com JavaScript `.jsx` / `.js` e Context API)
- **Vite 8** (build e servidor de desenvolvimento rápido)
- **Tailwind CSS v4** (`@tailwindcss/vite` com tokens visuais institucionais)
- **Oxlint** (padronização e verificação estática de código)

---

## Estrutura de Pastas (`frontend/src/`)

```text
frontend/src/
├── components/
│   ├── domain/          # Componentes de negócio (Chamada Rápida, Termômetro 75%, Bancadas, Usuários)
│   ├── feedback/        # Estados visuais (Loading, EmptyState, ErrorState e aviso LGPD)
│   ├── forms/           # Campos de formulário reutilizáveis e acessíveis
│   ├── layout/          # Cabeçalho (AppHeader), Menu Lateral (Sidebar) e Acessibilidade
│   ├── tables/          # Tabela de dados com busca, filtro e paginação (DataTable)
│   └── ui/              # Botões, Badges de situação/prioridade, Cards de métricas e Modais
├── context/
│   └── AcademicContext.jsx  # Estado global da aplicação (Professor/Aluno, turmas, chamada e alertas)
├── data/
│   └── academic-data.js     # Dados demonstrativos locais (mocks estruturados para integração com a API)
├── hooks/               # Hooks utilitários (responsividade mobile/tablet)
├── lib/                 # Roteador SPA leve (router.jsx) e biblioteca de ícones SVG (icons.jsx)
├── pages/
│   ├── auth/            # Login institucional e Configurações / LGPD
│   ├── academic/        # Gestão de Alunos, Turmas, Disciplinas e Módulos de Oficina
│   ├── teacher/         # Dashboard do Professor, Diário & Chamada Rápida, Análises, Alertas e Relatórios
│   └── student/         # Painel do Aluno, Notas & Boletim, Autoavaliação & Conquistas e Pedidos de Ajuda
├── services/            # Cliente HTTP (api.js) preparado para integração com o Back-end Python/FastAPI
├── utils/               # Filtros acadêmicos, cálculo de progresso prático, rubricas e acessibilidade
├── App.jsx              # Casca principal e mapeamento das rotas
└── main.jsx             # Ponto de entrada da aplicação React
```

---

## Telas Implementadas (Visões de Professor e Aluno)

### 1. Acesso Institucional
- **Login (`/`):** Entrada institucional com alternância rápida entre **Visão do Professor** e **Visão do Aluno**.

### 2. Visão do Professor
- **Dashboard (`/dashboard`):** Indicadores gerais (alunos ativos, média geral, frequência média e casos de atenção), gráfico de evolução mensal e distribuição de notas.
- **Alunos (`/alunos` e `/alunos/:id`):** Lista com busca, filtros por turma/situação e ficha individual do estudante com gráfico de evolução e linha do tempo de acompanhamento pedagógico.
- **Turmas (`/turmas`) e Disciplinas (`/disciplinas`):** Saúde acadêmica das turmas, frequência média, matriz curricular e vínculo de professores.
- **Diário & Oficina Prática (`/oficina`):**
  - **Chamada Rápida em 1 Clique:** Marcação rápida (`P` Presente, `F` Falta, `J` Justificada), botão *"Marcar todos presentes"* e alerta visual de frequência abaixo de **75%**.
  - **Módulos e Registro de Bancada:** Acompanhamento de atividades práticas de laboratório, normas de segurança (`NR-10` / `NR-12`) e check rápido de conclusão por aluno.
- **Desempenho (`/desempenho`) e Frequência (`/frequencia`):** Gráficos comparativos mensais e identificação preventiva de estudantes em risco.
- **Central de Alertas (`/alertas`):** Sinais acadêmicos filtrados por prioridade (`Alta`, `Média`, `Baixa`) com registro de acompanhamento docente.
- **Mural & Pedidos de Ajuda (`/comunicacao`):** Fila de resposta às dúvidas enviadas pelos alunos nas bancadas e publicação de avisos para as turmas.
- **Relatórios (`/relatorios`) e Configurações (`/configuracoes`):** Exportação de relatórios pedagógicos, gestão de usuários/acessos, parâmetros regimentais e conformidade com a **LGPD**.

### 3. Visão do Aluno
- **Meu Desempenho (`/aluno/painel`):** Média geral, frequência acumulada, práticas concluídas, evolução nas avaliações e últimos feedbacks dos professores.
- **Notas & Boletim (`/aluno/notas`):** Termômetro regimental de presença (mínimo 75%), notas por etapa (`AV1`, `AV2`, `Oficina Prática`, `Média Final`) e emissão do boletim individual.
- **Autoavaliação & Conquistas (`/aluno/autoavaliacao`):** Autoavaliação de competências técnicas/socioemocionais (escala 1 a 5 comparada à nota docente) e galeria de insígnias (gamificação).
- **Mural & Pedir Ajuda (`/aluno/ajuda`):** Canal direto para solicitar ajuda ao professor informando disciplina, bancada e prioridade, além do mural de avisos da turma.

---

## Como Executar Localmente

No terminal, dentro da pasta `frontend/`:

```bash
# 1. Instalar as dependências
npm install

# 2. Iniciar o servidor de desenvolvimento
npm run dev
```

A aplicação ficará disponível em `http://localhost:5173`.
