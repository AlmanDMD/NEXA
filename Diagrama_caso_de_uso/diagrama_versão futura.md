# Diagrama de Caso de Uso — NEXA (versão atualizada)

> Diagrama construído a partir do que **já está implementado no backend** (FastAPI, lotes S1–S4, até o BE-033).
> Os atores refletem exatamente os perfis de acesso (`UserRole`) aplicados nas rotas, e cada caso de uso corresponde a um ou mais endpoints existentes.

---

## 1. Atores

| Ator | Perfil no sistema | Descrição | Restrição de escopo |
|------|-------------------|-----------|---------------------|
| **Visitante** | — (não autenticado) | Pessoa que ainda não possui sessão ativa | Acessa apenas cadastro e login |
| **Estudante** | `STUDENT` | Aluno matriculado em uma turma | Consulta **somente os próprios dados** (proteção contra IDOR) |
| **Professor** | `TEACHER` | Instrutor responsável pelo diário de classe e pelas oficinas | Atua **somente nas turmas em que está alocado** |
| **Coordenador** | `COORDINATOR` | Coordenação pedagógica e gestão acadêmica | Visão global de todas as turmas |
| **Administrador** | `ADMIN` | Gestão total da plataforma | Visão global + **reabertura de turma encerrada** |
| **Motor de Risco** | Ator secundário (sistema) | `RiskEngineService`, executado automaticamente após mutações acadêmicas | Regras determinísticas e explicáveis |

### Generalização entre atores

O Coordenador herda todos os casos de uso do Professor (sem a restrição de turma) e acrescenta a gestão acadêmica. O Administrador herda tudo do Coordenador e acrescenta a reabertura de turmas encerradas.

```mermaid
flowchart BT
    U["👤 Usuário autenticado"]
    EST["👤 Estudante"]
    PROF["👤 Professor"]
    COORD["👤 Coordenador"]
    ADM["👤 Administrador"]

    EST -->|generaliza| U
    PROF -->|generaliza| U
    COORD -->|generaliza| PROF
    ADM -->|generaliza| COORD
```

---

## 2. Visão geral do sistema

```mermaid
flowchart LR
    VIS["👤 Visitante"]
    EST["👤 Estudante"]
    PROF["👤 Professor"]
    COORD["👤 Coordenador"]
    ADM["👤 Administrador"]
    RISK["⚙️ Motor de Risco"]

    subgraph NEXA["Sistema NEXA"]
        direction TB
        P1(["Autenticação e Sessão"])
        P2(["Estrutura Acadêmica"])
        P3(["Currículo Prático e Competências"])
        P4(["Diário de Classe: Aulas e Frequência"])
        P5(["Avaliações, Notas e Médias"])
        P6(["Atividades Práticas de Oficina"])
        P7(["Dashboard, Visão 360° e Risco Acadêmico"])
    end

    VIS --- P1
    EST --- P1
    EST --- P4
    EST --- P6

    PROF --- P1
    PROF --- P3
    PROF --- P4
    PROF --- P5
    PROF --- P6
    PROF --- P7

    COORD --- P2
    ADM --- P2

    P7 --- RISK
```

---

## 3. Diagramas por módulo

### 3.1 Autenticação e Sessão (EPIC-01)

```mermaid
flowchart LR
    VIS["👤 Visitante"]
    U["👤 Usuário autenticado<br/>(Estudante, Professor,<br/>Coordenador, Administrador)"]

    subgraph S1["Autenticação e Sessão"]
        direction TB
        UC01(["UC01 Registrar conta"])
        UC02(["UC02 Fazer login"])
        UC03(["UC03 Renovar sessão"])
        UC04(["UC04 Encerrar sessão"])
        UC05(["UC05 Consultar meu perfil"])
    end

    VIS --- UC01
    VIS --- UC02
    U --- UC03
    U --- UC04
    U --- UC05
```

### 3.2 Estrutura Acadêmica (EPIC-02)

```mermaid
flowchart LR
    PROF["👤 Professor"]
    COORD["👤 Coordenador"]
    ADM["👤 Administrador"]

    subgraph S2["Estrutura Acadêmica"]
        direction TB
        UC06(["UC06 Gerenciar cursos técnicos<br/>(cadastrar, consultar, atualizar, desativar)"])
        UC07(["UC07 Gerenciar disciplinas<br/>(cadastrar, atualizar)"])
        UC08(["UC08 Consultar disciplinas"])
        UC09(["UC09 Criar turma"])
        UC10(["UC10 Consultar turmas e alunos matriculados"])
        UC11(["UC11 Alterar status da turma"])
        UC12(["UC12 Reabrir turma encerrada"])
        UC13(["UC13 Matricular estudante"])
        UC14(["UC14 Alterar status da matrícula"])
        UC15(["UC15 Alocar professor em turma e disciplina"])
        UCA(["Registrar trilha de auditoria"])
    end

    COORD --- UC06
    COORD --- UC07
    COORD --- UC09
    COORD --- UC11
    COORD --- UC13
    COORD --- UC14
    COORD --- UC15
    PROF --- UC08
    PROF --- UC10
    ADM --- UC12

    UC12 -.->|"«extend»"| UC11
    UC14 -.->|"«include»"| UCA
```

> Coordenador e Administrador também acessam UC08 e UC10, por generalização do Professor.

### 3.3 Currículo Prático e Competências (EPIC-04)

```mermaid
flowchart LR
    PROF["👤 Professor"]
    COORD["👤 Coordenador"]

    subgraph S3["Currículo Prático e Competências"]
        direction TB
        UC16(["UC16 Cadastrar módulo prático"])
        UC17(["UC17 Listar módulos da disciplina"])
        UC18(["UC18 Cadastrar competência no catálogo"])
        UC19(["UC19 Consultar catálogo de competências"])
        UC20(["UC20 Vincular competência a módulo"])
        UC21(["UC21 Consultar competências do módulo"])
    end

    PROF --- UC16
    PROF --- UC17
    PROF --- UC19
    PROF --- UC20
    PROF --- UC21
    COORD --- UC18
```

### 3.4 Diário de Classe: Aulas e Frequência (EPIC-03)

```mermaid
flowchart LR
    EST["👤 Estudante"]
    PROF["👤 Professor"]
    RISK["⚙️ Motor de Risco"]

    subgraph S4["Diário de Classe: Aulas e Frequência"]
        direction TB
        UC22(["UC22 Registrar aula ministrada"])
        UC23(["UC23 Consultar diário de aulas da turma"])
        UC24(["UC24 Registrar chamada em lote"])
        UC25(["UC25 Consultar extrato de frequência"])
        UCG(["Verificar período letivo ativo"])
        UCF(["Recalcular frequência da matrícula"])
        UCR(["Reavaliar risco acadêmico"])
    end

    PROF --- UC22
    PROF --- UC23
    PROF --- UC24
    PROF --- UC25
    EST --- UC25

    UC22 -.->|"«include»"| UCG
    UC24 -.->|"«include»"| UCG
    UC24 -.->|"«include»"| UCF
    UC24 -.->|"«include»"| UCR
    UCR --- RISK
```

> No UC25, o Estudante consulta apenas a **própria** frequência.

### 3.5 Avaliações, Notas e Médias (EPIC-03)

```mermaid
flowchart LR
    PROF["👤 Professor"]
    RISK["⚙️ Motor de Risco"]

    subgraph S5["Avaliações, Notas e Médias"]
        direction TB
        UC26(["UC26 Cadastrar avaliação<br/>(prova, microavaliação, projeto)"])
        UC27(["UC27 Listar avaliações"])
        UC28(["UC28 Lançar notas e recuperações em lote"])
        UC29(["UC29 Calcular médias ponderadas da turma"])
        UC30(["UC30 Consultar boletim consolidado"])
        UCG(["Verificar período letivo ativo"])
        UCA(["Registrar retificação em auditoria"])
        UCR(["Reavaliar risco acadêmico"])
    end

    PROF --- UC26
    PROF --- UC27
    PROF --- UC28
    PROF --- UC29
    PROF --- UC30

    UC26 -.->|"«include»"| UCG
    UC28 -.->|"«include»"| UCG
    UC29 -.->|"«include»"| UCG
    UCA -.->|"«extend»<br/>(nota já existente)"| UC28
    UC29 -.->|"«include»"| UCR
    UCR --- RISK
```

### 3.6 Atividades Práticas de Oficina (EPIC-04)

```mermaid
flowchart LR
    EST["👤 Estudante"]
    PROF["👤 Professor"]
    RISK["⚙️ Motor de Risco"]

    subgraph S6["Atividades Práticas de Oficina"]
        direction TB
        UC31(["UC31 Cadastrar atividade prática com rubricas"])
        UC32(["UC32 Listar atividades do módulo"])
        UC33(["UC33 Avaliar entrega por rubricas"])
        UC34(["UC34 Consultar tarefas pendentes e em atraso"])
        UCG(["Verificar período letivo ativo"])
        UCP(["Gerar entregas pendentes da turma"])
        UCR(["Reavaliar risco acadêmico"])
    end

    PROF --- UC31
    PROF --- UC32
    PROF --- UC33
    PROF --- UC34
    EST --- UC34

    UC31 -.->|"«include»"| UCG
    UC31 -.->|"«include»"| UCP
    UC33 -.->|"«include»"| UCG
    UC33 -.->|"«include»"| UCR
    UCR --- RISK
```

> No UC34, o Estudante consulta apenas as **próprias** tarefas. Status de entrega: `PENDING`, `LATE` (calculado dinamicamente), `SUBMITTED` e `EVALUATED`.

### 3.7 Dashboard, Visão 360° e Risco Acadêmico (EPIC-05)

```mermaid
flowchart LR
    PROF["👤 Professor"]
    RISK["⚙️ Motor de Risco"]

    subgraph S7["Dashboard, Visão 360° e Risco Acadêmico"]
        direction TB
        UC35(["UC35 Consultar dashboard da turma"])
        UC36(["UC36 Consultar ficha 360° do estudante"])
        UC37(["UC37 Executar avaliação de risco da turma"])
        UC38(["UC38 Listar alunos em risco"])
        UCJ(["Gerar justificativa explicável"])
        UCS(["Sugerir ação pedagógica"])
    end

    PROF --- UC35
    PROF --- UC36
    PROF --- UC37
    PROF --- UC38

    UC37 -.->|"«include»"| UCJ
    UC38 -.->|"«include»"| UCS
    UC37 --- RISK
```

> Regras do Motor de Risco: presença < 75% → `CRITICAL`; presença entre 75% e 78% → `HIGH`; 2 tarefas atrasadas → `MODERATE`; 3 ou mais → `HIGH`; média abaixo da nota de corte → `HIGH`. Todo alerta traz o aviso ético de que **não constitui reprovação automática**.

---

## 4. Matriz Ator × Caso de Uso

Legenda: **X** = acesso total · **P** = apenas os próprios dados · **T** = apenas turmas em que está alocado

| Caso de uso | Visitante | Estudante | Professor | Coordenador | Administrador |
|-------------|:---------:|:---------:|:---------:|:-----------:|:-------------:|
| UC01 Registrar conta | X | | | | |
| UC02 Fazer login | X | | | | |
| UC03–UC05 Sessão e perfil | | X | X | X | X |
| UC06 Gerenciar cursos técnicos | | | | X | X |
| UC07 Gerenciar disciplinas | | | | X | X |
| UC08 Consultar disciplinas | | | X | X | X |
| UC09 Criar turma | | | | X | X |
| UC10 Consultar turmas e alunos | | | X | X | X |
| UC11 Alterar status da turma | | | | X | X |
| UC12 Reabrir turma encerrada | | | | | X |
| UC13 Matricular estudante | | | | X | X |
| UC14 Alterar status da matrícula | | | | X | X |
| UC15 Alocar professor | | | | X | X |
| UC16–UC17 Módulos práticos | | | X | X | X |
| UC18 Cadastrar competência | | | | X | X |
| UC19–UC21 Consultar/vincular competências | | | X | X | X |
| UC22–UC24 Aulas e chamada | | | T | X | X |
| UC25 Extrato de frequência | | P | T | X | X |
| UC26–UC30 Avaliações, notas e médias | | | T | X | X |
| UC31–UC33 Atividades práticas | | | T | X | X |
| UC34 Tarefas pendentes | | P | T | X | X |
| UC35–UC38 Dashboard, 360° e risco | | | T | X | X |

---

## 5. Regras transversais

| Regra | Casos de uso afetados | Comportamento |
|-------|-----------------------|---------------|
| **Bloqueio de período letivo encerrado** (BE-029) | UC22, UC24, UC26, UC28, UC29, UC31, UC33 | Turma `COMPLETED` ou `ARCHIVED` → HTTP 422 `CLASS_PERIOD_CLOSED`. Só volta a aceitar alterações se for reaberta (UC12). |
| **Reavaliação automática de risco** (BE-032) | UC24, UC29, UC33 | O Motor de Risco recalcula os alertas da matrícula ou da turma, sem duplicar alertas abertos e encerrando os que normalizaram. |
| **Auditoria** | UC14, UC28 | Mudança de status de matrícula e retificação de nota existente são gravadas em `audit_logs`. |
| **Isolamento de dados** | UC25, UC34, UC35–UC38 | O Estudante vê só os próprios dados; o Professor só acessa as turmas em que está alocado. |

---

## 6. Diferenças em relação à versão anterior

| Versão anterior | Versão atualizada |
|-----------------|-------------------|
| Atores genéricos: "Gestores", "Alunos" e "Coordenação" | Atores iguais aos perfis reais do sistema: Estudante, Professor, Coordenador e Administrador, mais Visitante e o Motor de Risco |
| "Gestores" agrupava Professores e Secretaria | O Professor ficou separado da gestão acadêmica, que é do Coordenador e do Administrador. O perfil "Secretaria" não existe no sistema. |
| Casos de uso só com verbos (Enviar, Editar, Excluir...) | Casos de uso com verbo + objeto, ligados às funcionalidades entregues |
| "Receber" (avisos/materiais) | Removido: ainda não há envio de avisos ou materiais implementado |
| "Excluir" | Só existe a desativação lógica de curso (soft delete), dentro de UC06 |
| Sem relações entre casos de uso | Foram incluídas as relações «include» e «extend» e a generalização entre atores |
