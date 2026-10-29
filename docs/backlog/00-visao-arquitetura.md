# 🏛️ Arquitetura, Epics e Governança do Projeto NEXA
## Sistema Inteligente de Monitoramento do Desempenho Acadêmico — SENAI

---

## 1. Contexto e Problema Identificado
Os sistemas acadêmicos tradicionais limitam-se ao registro estático de notas e frequência. No contexto de cursos técnicos do SENAI (onde o ensino é modular e focado em habilidades práticas de oficina, como **Metrologia, Desenho Técnico, Tornearia e Ajustagem Mecânica**), existe uma lacuna crítica:
- **Dificuldade na identificação antecipada de alunos com defasagem de aprendizado.**
- **Falta de integração entre autoavaliação do aluno e avaliação prática do professor.**
- **Insegurança e ruído na comunicação de dificuldades (alunos têm receio de expor dúvidas publicamente).**
- **Sobrecarga dos professores com planilhas paralelas.**

---

## 2. Decisões Arquiteturais e Stack Tecnológica
- **Front-end**: React 19 + TypeScript + Vite + Tailwind CSS v4 + Lucide React + TanStack Query (para cache e gerenciamento de estado de requisições).
- **Back-end**: Node.js com TypeScript, framework modular (Fastify/Express), arquitetura em camadas (*Controllers -> Services -> Repositories*), validação estrita com Zod.
- **Banco de Dados**: PostgreSQL 16 com Prisma ORM, migrations incrementais versionadas, seeds realistas industriais.
- **Segurança & LGPD**: Autenticação JWT com HttpOnly Cookies, RBAC granular (`ADMIN`, `COORDINATOR`, `TEACHER`, `STUDENT`), observações pedagógicas com criptografia/acesso restrito, logs de auditoria para ações sensíveis.

---

## 3. Mapa de Epics Unificados

| ID do Epic | Nome do Epic | Descrição |
|---|---|---|
| **EPIC-01** | **Autenticação, Perfis (RBAC) & Segurança** | Controle de acesso baseado em papéis, sessões seguras e proteção LGPD. |
| **EPIC-02** | **Gestão Acadêmica & Estrutura SENAI** | Cadastro de turmas, matrículas, disciplinas e módulos práticos de aprendizagem. |
| **EPIC-03** | **Diário de Classe: Notas & Frequência** | Lançamento rápido de presença/faltas, microavaliações e cálculo ponderado de médias. |
| **EPIC-04** | **Atividades Práticas de Oficina & Competências** | Registro de tarefas em bancada/máquina (Tornearia, Metrologia), critérios de precisão e rubricas. |
| **EPIC-05** | **Dashboard Híbrido do Professor & Visão 360°** | Painel analítico de turma, alertas precoces explicáveis e identificação de alunos em risco. |
| **EPIC-06** | **Portal de Autonomia do Aluno & Pendências** | Visão do estudante de seu progresso, tarefas atrasadas, notas parciais e evolução de habilidades. |
| **EPIC-07** | **Autoavaliação & Motor de Diagnóstico Explicável** | Comparativo entre a percepção do aluno e a evidência do professor, com alertas não rotuladores. |
| **EPIC-08** | **Comunicação Oficial & Solicitações Confidenciais** | Mural de avisos da turma, mensagens internas e canal seguro de pedido de ajuda pedagógica. |
| **EPIC-09** | **Gamificação Pedagógica Transparente & Níveis** | Badges por competências dominadas e pontuação justa sem ranking punitivo/expositivo. |
| **EPIC-10** | **Relatórios, Governança de Dados & Qualidade** | Exportações para conselho de classe, logs de auditoria e rotinas de manutenção. |

---

## 4. Estratégia de Desenvolvimento em Ondas (Lotes de 10 cards)
Para viabilizar o desenvolvimento gradual solicitado pelo professor:
- **Onda 1 (Cards 01 a 10 de cada área)**: *Fundação, Schemas Base e Design System*.
- **Onda 2 (Cards 11 a 20 de cada área)**: *Autenticação, Matrículas e Estrutura de Turmas*.
- **Onda 3 (Cards 21 a 30 de cada área)**: *Lançamento de Aulas, Frequência e Atividades Práticas*.
- **Onda 4 (Cards 31 a 40 de cada área)**: *Dashboards, Portais de Consulta e Indicadores de Risco*.
- **Onda 5 (Cards 41 a 50 de cada área)**: *Autoavaliação, Diagnósticos, Mensageria, Gamificação e Auditoria*.
