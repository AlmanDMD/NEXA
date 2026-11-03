# 📋 Guia Completo de Estruturação e Governança — GitHub Projects (v2) NEXA

Este documento apresenta a arquitetura de gerenciamento de trabalho da organização **`AlmanDMD`** e do repositório **`AlmanDMD/NEXA`** utilizando **GitHub Projects (v2)**, cobrindo tanto a automação via **API GraphQL / GitHub CLI (`gh`)** quanto o passo a passo completo na **interface web do GitHub**.

---

## 1. Arquitetura dos 5 GitHub Projects (v2)

A estrutura é composta por **4 Projetos Setoriais** (foco operacional de cada camada) e **1 Projeto Geral** (visão executiva e integrada de todas as squads):

| # | Nome Padronizado do Projeto | Tipo | Filtro / Escopo de Itens | Campo Customizado |
|---|---|---|---|---|
| 1 | **`NEXA – Frontend`** | Setorial | Issues e PRs com label `area:frontend` (`[FE-...]`) | Padrão |
| 2 | **`NEXA – Backend`** | Setorial | Issues e PRs com label `area:backend` (`[BE-...]`) | Padrão |
| 3 | **`NEXA – Banco de Dados`** | Setorial | Issues e PRs com label `area:database` (`[DB-...]`) | Padrão |
| 4 | **`NEXA – Documentação`** | Setorial | Issues e PRs com label `area:docs` (`[DOC-...]`) | Padrão |
| 5 | **`NEXA – Geral`** | Consolidado | **100% dos itens** dos 4 projetos setoriais | `Squad` (*Single select*): `Frontend`, `Backend`, `Banco de Dados`, `Documentação` |

---

## 2. Colunas de `Status` Obrigatórias (Nos 5 Projetos)

Em todos os 5 projetos, o campo nativo **`Status`** está configurado exatamente nesta ordem e nomenclatura:

1. **`BACKLOG`** *(Cinza)* — Itens mapeados e priorizados aguardando início do desenvolvimento.
2. **`IN PROGRESS`** *(Azul)* — Itens em desenvolvimento ativo pela equipe.
3. **`REFINEMENT`** *(Amarelo)* — Itens em detalhamento técnico, alinhamento de contrato ou desbloqueio.
4. **`IN REVIEW`** *(Roxo)* — Pull Request aberto aguardando revisão de código (*Code Review*) e testes.
5. **`DONE`** *(Verde)* — Critérios de aceitação e Definição de Pronto (*DoD*) 100% concluídos.

---

## 3. Passo a Passo na Interface Web do GitHub (Views, Board e Workflows)

Como a API GraphQL do GitHub cria os projetos, vincula o repositório, configura as colunas de `Status`, cria o campo `Squad` e popula todos os 70 cards automaticamente, restam apenas os ajustes visuais de **Views (Abas)** e **Workflows Nativos** na interface web do GitHub:

### 3.1. Converter a View Principal para Formato `Board` (Kanban) nos 5 Projetos
1. Acesse cada um dos 5 projetos em `https://github.com/orgs/AlmanDMD/projects`.
2. Na aba **`View 1`** (canto superior esquerdo), clique na seta `▾` ao lado do nome da view.
3. Selecione o layout **Board** (ícone de colunas Kanban).
4. Clique em **Column field** (ou *Group by*) e confirme que está selecionado **`Status`**.
5. Renomeie a aba para **`Kanban`** (nos projetos setoriais) ou **`Visão Geral`** (no projeto `NEXA – Geral`).
6. Clique no botão **Save** (ou `Save changes`) no canto superior direito.

---

### 3.2. Configurar as 5 Visões (Views) no Projeto `NEXA – Geral`

No projeto **`NEXA – Geral`**, configure as abas para que cada Squad tenha sua visão isolada e a coordenação tenha a visão consolidada:

1. **Aba 1 — `Visão Geral (Por Squad)`**:
   - Layout: **Table** ou **Board**.
   - Se **Table**: Clique em **Group by** -> selecione **`Squad`**. Assim todos os cards aparecem agrupados em 4 blocos (*Frontend*, *Backend*, *Banco de Dados* e *Documentação*).
   - Clique em **Save**.

2. **Aba 2 — `Squad — Frontend`**:
   - Clique em **`+ New view`** -> escolha **Board**.
   - Renomeie a view para **`Squad — Frontend`**.
   - Na barra de filtro (`Filter by keyword or by field`), digite:
     ```text
     Squad:Frontend
     ```
     *(ou `label:area:frontend`)*.
   - Pressione **Enter** e clique em **Save**.

3. **Aba 3 — `Squad — Backend`**:
   - Clique em **`+ New view`** -> escolha **Board**.
   - Renomeie para **`Squad — Backend`**.
   - No filtro, digite:
     ```text
     Squad:Backend
     ```
   - Pressione **Enter** e clique em **Save**.

4. **Aba 4 — `Squad — Banco de Dados`**:
   - Clique em **`+ New view`** -> escolha **Board**.
   - Renomeie para **`Squad — Banco de Dados`**.
   - No filtro, digite:
     ```text
     Squad:"Banco de Dados"
     ```
   - Pressione **Enter** e clique em **Save**.

5. **Aba 5 — `Squad — Documentação`**:
   - Clique em **`+ New view`** -> escolha **Board**.
   - Renomeie para **`Squad — Documentação`**.
   - No filtro, digite:
     ```text
     Squad:Documentação
     ```
   - Pressione **Enter** e clique em **Save**.

---

### 3.3. Configurar os Workflows Automáticos Nativos (Nos 5 Projetos)

Para que novos itens entrem automaticamente em **`BACKLOG`** e itens fechados/mergeados vão para **`DONE`**:

1. Dentro do projeto, clique no botão **`⋯`** (canto superior direito) -> **`Workflows`** (ou clique direto no botão `Workflows` no topo).
2. **Workflow 1: `Item added to project` (Novos itens entram em BACKLOG)**
   - Clique em **Item added to project** no menu lateral esquerdo.
   - Clique em **Edit** (canto superior direito).
   - Em *Set value*, selecione **`Status: BACKLOG`**.
   - Clique em **Save and turn on workflow**.
3. **Workflow 2: `Item closed` (Issues/PRs fechados vão para DONE)**
   - Clique em **Item closed** no menu lateral esquerdo.
   - Confirme que *Set value* está em **`Status: DONE`**.
   - Caso não esteja ativo, clique em **Edit** -> selecione **`Status: DONE`** -> **Save and turn on workflow**.
4. **Workflow 3: `Pull request merged` (PRs mergeados vão para DONE)**
   - Clique em **Pull request merged** no menu lateral esquerdo.
   - Confirme que *Set value* está em **`Status: DONE`** e ative o workflow.
5. **Workflow 4: `Auto-add to project` (Adição automática de novas Issues/PRs do repositório `NEXA`)**
   - Clique em **Auto-add to project** no menu lateral esquerdo -> **Edit**.
   - Selecione o repositório **`AlmanDMD/NEXA`**.
   - Defina o filtro conforme o projeto:
     - Em **`NEXA – Frontend`**: `is:issue,pr label:area:frontend`
     - Em **`NEXA – Backend`**: `is:issue,pr label:area:backend`
     - Em **`NEXA – Banco de Dados`**: `is:issue,pr label:area:database`
     - Em **`NEXA – Documentação`**: `is:issue,pr label:area:docs`
     - Em **`NEXA – Geral`**: `is:issue,pr` *(recebe automaticamente todos os itens de todas as áreas!)*
   - Clique em **Save and turn on workflow**.

---

## 4. Reprodução Automatizada via Script / CLI / API GraphQL

Toda a criação dos 5 projetos, vinculação do repositório `AlmanDMD/NEXA`, padronização das 5 colunas de `Status`, criação do campo `Squad` e sincronização das issues foi automatizada no script:

- **Arquivo**: [`scripts/setup-github-projects.js`](../../scripts/setup-github-projects.js)
- **Como executar**:
  ```bash
  node scripts/setup-github-projects.js
  ```

### Comandos Equivalentes via GitHub CLI (`gh project`)

Caso deseje executar manualmente via **GitHub CLI (`gh`)**:

```bash
# 1. Autenticar com escopo de projetos
gh auth refresh -s project,repo

# 2. Criar os 5 projetos na organização AlmanDMD
gh project create --owner AlmanDMD --title "NEXA – Frontend"
gh project create --owner AlmanDMD --title "NEXA – Backend"
gh project create --owner AlmanDMD --title "NEXA – Banco de Dados"
gh project create --owner AlmanDMD --title "NEXA – Documentação"
gh project create --owner AlmanDMD --title "NEXA – Geral"

# 3. Vincular o repositório NEXA a cada projeto (substituir <NUM> pelo número do projeto)
gh project link <NUM> --owner AlmanDMD --repo AlmanDMD/NEXA

# 4. Criar o campo Single Select 'Squad' no projeto NEXA – Geral
gh project field-create <NUM_GERAL> \
  --owner AlmanDMD \
  --name "Squad" \
  --data-type "SINGLE_SELECT" \
  --single-select-options "Frontend,Backend,Banco de Dados,Documentação"
```

