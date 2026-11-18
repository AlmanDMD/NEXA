# 📚 Backlog de Documentação Técnica, Acadêmica e Governança — Projeto NEXA
## 20 Cards Estruturados e Encadeados de Documentação (`DOC-001` a `DOC-020`)

Este documento reúne todos os 20 entregáveis de documentação de engenharia de software, arquitetura, banco de dados, segurança LGPD, qualidade e apresentação para a banca avaliadora SENAI.

---

### Resumo dos Lotes / Sprints de Implementação
- **Lote 1 / Sprint 1 (DOC-001 a DOC-005)**: Escopo Executivo, Requisitos RF/RNF, Personas SENAI, Regras de Negócio e Arquitetura C4 Model.
- **Lote 2 / Sprint 2 (DOC-006 a DOC-010)**: Guia de Estilo UI/UX, Padrões de Código/GitFlow, DER Oficial, Dicionário de Dados e Guia de Setup Local.
- **Lote 3 / Sprint 3 (DOC-011 a DOC-013)**: Catálogo OpenAPI/Swagger, Matriz RBAC + Relatório LGPD e Guia Pedagógico de Rubricas SENAI.
- **Lote 4 / Sprint 4 (DOC-014 a DOC-016)**: Especificação da Heurística de Risco Explicável, Plano de Testes Integrados e Manual de Operação DevOps.
- **Lote 5 / Sprint 5 (DOC-017 a DOC-020)**: Manual do Professor/Coordenador, Guia do Estudante, Relatório de Auditoria Final e Roteiro de Pitch/Defesa para a Banca.

---

### Tabela Geral Encadeada (20 Cards)

| ID | Título | Epic | Prioridade | Estimativa | Lote / Sprint | Dependências |
|---|---|---|---|---|---|---|
| `DOC-001` | Elaborar Documento de Visão do Produto e Justificativa de Negócio | EPIC-01 | P0 | 3 SP | Lote 1 (S1) | `Nenhuma` |
| `DOC-002` | Mapear Especificação de Requisitos Funcionais (RF) e Não-Funcionais (RNF) | EPIC-01 | P0 | 3 SP | Lote 1 (S1) | `DOC-001` |
| `DOC-003` | Definir Personas, Matriz de Perfis de Usuário e Jornadas de Uso | EPIC-01 | P1 | 2 SP | Lote 1 (S1) | `DOC-001` |
| `DOC-004` | Detalhar Histórias de Usuário Globais e Critérios de Aceitação | EPIC-01 | P0 | 3 SP | Lote 1 (S1) | `DOC-002` |
| `DOC-005` | Atualizar Diagrama de Casos de Uso Completo em Mermaid | EPIC-01 | P0 | 2 SP | Lote 1 (S1) | `DOC-002` |
| `DOC-006` | Elaborar Diagrama de Atividades dos Fluxos Críticos (Chamada e Avaliação) | EPIC-03 | P1 | 3 SP | Lote 2 (S2) | `DOC-005` |
| `DOC-007` | Elaborar Diagrama de Arquitetura em Camadas e Visão de Containers C4 | EPIC-01 | P0 | 3 SP | Lote 2 (S2) | `DOC-001` |
| `DOC-008` | Elaborar Diagrama Entidade-Relacionamento (DER) Oficial do Banco de Dados | EPIC-01 | P0 | 3 SP | Lote 2 (S2) | `DOC-002` |
| `DOC-009` | Construir Dicionário de Dados Completo com Tipos, Chaves e Restrições | EPIC-01 | P0 | 3 SP | Lote 2 (S2) | `DOC-008` |
| `DOC-010` | Elaborar Manual de Instalação, Configuração Local e Docker | EPIC-01 | P0 | 2 SP | Lote 2 (S2) | `DOC-001, DB-003, BE-001, FE-001` |
| `DOC-011` | Elaborar README.md Principal do Repositório com Badges e Guia Rápido | EPIC-10 | P0 | 2 SP | Lote 3 (S3) | `DOC-001, DOC-007, DOC-010` |
| `DOC-012` | Criar Guia de Variáveis de Ambiente e Segurança (.env.example) | EPIC-01 | P0 | 1 SP | Lote 3 (S3) | `DOC-010, DB-003, BE-005, FE-010` |
| `DOC-013` | Documentar Especificação de API REST com OpenAPI / Swagger | EPIC-10 | P0 | 3 SP | Lote 3 (S3) | `DOC-002, BE-020, BE-030, BE-050` |
| `DOC-014` | Elaborar Manual de Usabilidade do Professor e Diário Eletrônico | EPIC-05 | P1 | 5 SP | Lote 4 (S4) | `DOC-003, FE-022, FE-025, FE-031, FE-034, FE-045` |
| `DOC-015` | Elaborar Manual de Usabilidade do Aluno (Portal e Autoavaliação) | EPIC-06 | P1 | 3 SP | Lote 4 (S4) | `DOC-003, FE-035, FE-036, FE-041, FE-044, FE-047` |
| `DOC-016` | Elaborar Plano Estratégico de Testes e Relatório de Qualidade | EPIC-10 | P1 | 3 SP | Lote 4 (S4) | `DOC-002, DB-050, BE-020, BE-030, BE-040, FE-030, FE-050` |
| `DOC-017` | Elaborar Relatório de Conformidade LGPD, Segurança e Plano de Backup | EPIC-10 | P1 | 3 SP | Lote 5 (S5) | `DOC-002, DB-009, DB-043, DB-048, DB-049, BE-045, BE-048` |
| `DOC-018` | Documentar Registro de Decisões de Arquitetura (ADRs) e Guia de Deploy | EPIC-10 | P1 | 2 SP | Lote 5 (S5) | `DOC-007, DOC-010, DOC-012, DB-050, BE-050, FE-050` |
| `DOC-019` | Preparar Slides, Roteiro de Demonstração e Pitch da Banca Final SENAI | EPIC-10 | P0 | 5 SP | Lote 5 (S5) | `DOC-001, DOC-014, DOC-015, DOC-016, FE-050, BE-050, DB-050` |
| `DOC-020` | Redigir Relatório Final Consolidado do Projeto de Conclusão de Semestre | EPIC-10 | P0 | 8 SP | Lote 5 (S5) | `DOC-001, DOC-005, DOC-008, DOC-009, DOC-013, DOC-016, DOC-017, DOC-018, DOC-019, DB-050, BE-050, FE-050` |

---

## Detalhamento Completo e Encadeado dos 20 Cards

### [DOC-001] Elaborar Documento de Visão do Produto e Justificativa de Negócio
- **ID**: `DOC-001`
- **Título**: Elaborar Documento de Visão do Produto e Justificativa de Negócio
- **Área**: Documentação
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `Início da Trilha` | ➡️ Próximo: `DOC-002`
- **Dependências Diretas**: `Nenhuma`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: documentacao
- **Objetivo**: Formalizar o propósito, justificativa pedagógica e benefícios esperados do Sistema NEXA para o contexto SENAI.
- **Descrição**: Redigir documento em docs/academico/visao-produto.md contendo: declaração do problema, contextualização do ensino técnico modular SENAI, proposta de valor, público-alvo (professores, alunos, coordenação) e critérios de sucesso do projeto.
- **História de Usuário**: Como Banca Avaliadora Acadêmica, quero ler o documento de visão do produto, para entender a motivação e o impacto institucional do sistema.
- **Critérios de Aceitação**:
- Problema dos sistemas tradicionais e defasagem no acompanhamento de oficinas claramente descritos.
- Objetivos gerais e específicos quantificados.
- Alinhamento pedagógico com a metodologia de competências SENAI.
- **Definição de Pronto (DoD)**: Documento redigido, formatado em Markdown e revisado pelo Orientador/Tech Lead.
- **Observações Técnicas**: Evitar prometer redução garantida de reprovações; apresentar como meta a ser avaliada.

---

### [DOC-002] Mapear Especificação de Requisitos Funcionais (RF) e Não-Funcionais (RNF)
- **ID**: `DOC-002`
- **Título**: Mapear Especificação de Requisitos Funcionais (RF) e Não-Funcionais (RNF)
- **Área**: Documentação
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `DOC-001` | ➡️ Próximo: `DOC-003`
- **Dependências Diretas**: `DOC-001`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: documentacao
- **Objetivo**: Documentar com rigor analítico todos os requisitos funcionais e critérios não-funcionais do sistema.
- **Descrição**: Elaborar docs/academico/requisitos.md listando pelo menos 30 Requisitos Funcionais (RF-01 a RF-30) e 15 Requisitos Não-Funcionais (RNF-01 a RNF-15 cobrindo segurança, performance, LGPD, usabilidade e acessibilidade WCAG).
- **História de Usuário**: Como Analista de Sistemas, quero uma especificação completa de requisitos, para guiar o desenvolvimento e validar os critérios de aceitação.
- **Critérios de Aceitação**:
- Requisitos identificados com códigos únicos e prioridades MoSCoW (Must, Should, Could, Won't).
- RNFs detalhados com métricas objetivas (ex: tempo de resposta da API < 200ms).
- Rastreabilidade com os épicos do projeto.
- **Definição de Pronto (DoD)**: Documento de requisitos aprovado.
- **Observações Técnicas**: Seguir padrão de engenharia de software acadêmica.

---

### [DOC-003] Definir Personas, Matriz de Perfis de Usuário e Jornadas de Uso
- **ID**: `DOC-003`
- **Título**: Definir Personas, Matriz de Perfis de Usuário e Jornadas de Uso
- **Área**: Documentação
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `DOC-002` | ➡️ Próximo: `DOC-004`
- **Dependências Diretas**: `DOC-001`
- **Prioridade**: P1 | **Estimativa**: 2 SP | **Tipo**: documentacao
- **Objetivo**: Criar perfis representativos dos usuários reais para guiar as decisões de design e usabilidade.
- **Descrição**: Documentar em docs/design/personas-jornadas.md: Persona do Estudante de Oficina (ex: 'Lucas, 19 anos, aprendendo tornearia com dificuldades em tolerância'), Persona do Professor de Prática (ex: 'Carlos, 45 anos, sobrecarregado com anotações em prancheta') e Coordenador. Mapear mapa de empatia e jornada do usuário.
- **História de Usuário**: Como Designer de Interface, quero me basear em personas reais, para projetar fluxos rápidos que funcionem mesmo dentro da oficina mecânica.
- **Critérios de Aceitação**:
- Mínimo de 3 personas detalhadas com dores, objetivos e contexto de uso.
- Jornada do professor registrando atividades práticas mapeada passo a passo.
- Jornada do aluno consultando pendências e solicitando mentoria.
- **Definição de Pronto (DoD)**: Documento de personas entregue e utilizado como base para o Front-end.
- **Observações Técnicas**: Considerar o cenário de uso do professor em tablet ou celular durante a aula prática.

---

### [DOC-004] Detalhar Histórias de Usuário Globais e Critérios de Aceitação
- **ID**: `DOC-004`
- **Título**: Detalhar Histórias de Usuário Globais e Critérios de Aceitação
- **Área**: Documentação
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `DOC-003` | ➡️ Próximo: `DOC-005`
- **Dependências Diretas**: `DOC-002`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: documentacao
- **Objetivo**: Consolidar o catálogo mestre de User Stories para o backlog acadêmico.
- **Descrição**: Criar docs/academico/historias-usuario.md estruturando histórias no formato 'Como [ator], quero [ação], para [benefício]' com cenários de teste Gherkin (Dado/Quando/Então) para os fluxos principais do sistema.
- **História de Usuário**: Como Equipe de Desenvolvimento, quero histórias de usuário bem escritas, para planejar e testar as entregas das sprints.
- **Critérios de Aceitação**:
- Mínimo de 20 histórias detalhadas cobrindo todos os módulos do MVP.
- Critérios de aceitação verificáveis e mensuráveis.
- Vínculo direto com os IDs das issues do GitHub.
- **Definição de Pronto (DoD)**: Catálogo de histórias de usuário finalizado.
- **Observações Técnicas**: Evitar histórias genéricas; especificar contextos técnicos.

---

### [DOC-005] Atualizar Diagrama de Casos de Uso Completo em Mermaid
- **ID**: `DOC-005`
- **Título**: Atualizar Diagrama de Casos de Uso Completo em Mermaid
- **Área**: Documentação
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 1 (S1)
- **Sequência na Squad**: ⬅️ Anterior: `DOC-004` | ➡️ Próximo: `DOC-006`
- **Dependências Diretas**: `DOC-002`
- **Prioridade**: P0 | **Estimativa**: 2 SP | **Tipo**: documentacao
- **Objetivo**: Evoluir o diagrama inicial preliminar existente na pasta Diagrama_caso_de_uso para uma representação formal UML completa.
- **Descrição**: Atualizar Diagrama_caso_de_uso/diagrama-caso-de-uso.md em Mermaid, detalhando os casos de uso para Aluno (Consultar Desempenho, Autoavaliar Habilidades, Solicitar Ajuda Confidencial), Professor (Lançar Presença Rápida, Avaliar Atividade Prática, Registrar Nota Pedagógica) e Coordenação.
- **História de Usuário**: Como Banca de TCC, quero ver o diagrama de casos de uso formalizado, para avaliar a completude das interações do sistema.
- **Critérios de Aceitação**:
- Diagrama Mermaid renderizando sem erros de sintaxe.
- Atores bem definidos com relações de herança e fronteiras de sistema claras.
- Matriz de rastreabilidade Ator x Caso de Uso atualizada.
- **Definição de Pronto (DoD)**: Arquivo diagrama-caso-de-uso.md atualizado no repositório.
- **Observações Técnicas**: Substituir os verbos genéricos anteriores (ex: 'Enviar', 'Editar') por ações de negócio concretas.

---

### [DOC-006] Elaborar Diagrama de Atividades dos Fluxos Críticos (Chamada e Avaliação)
- **ID**: `DOC-006`
- **Título**: Elaborar Diagrama de Atividades dos Fluxos Críticos (Chamada e Avaliação)
- **Área**: Documentação
- **Epic**: EPIC-03: Diário de Classe: Notas & Frequência
- **Lote / Sprint**: Lote 2 (S2)
- **Sequência na Squad**: ⬅️ Anterior: `DOC-005` | ➡️ Próximo: `DOC-007`
- **Dependências Diretas**: `DOC-005`
- **Prioridade**: P1 | **Estimativa**: 3 SP | **Tipo**: documentacao
- **Objetivo**: Modelar a lógica visual sequencial dos dois processos mais repetitivos do sistema: a chamada rápida e o registro prático de oficina.
- **Descrição**: Elaborar docs/diagramas/atividades.md em Mermaid com diagramas de atividade (swimlanes/raias) mostrando as etapas, pontos de decisão (if/else), persistência e feedback ao professor.
- **História de Usuário**: Como Desenvolvedor, quero consultar o diagrama de atividades, para entender o fluxo de dados e exceções de regras de negócio antes de codar a tela.
- **Critérios de Aceitação**:
- Fluxo de Chamada Rápida com decisão de aluno atrasado/justificado modelado.
- Fluxo de Registro Prático com tolerância de medidas e critério de aprovação modelado.
- Raias separando visão do Usuário, Frontend, Backend e Banco.
- **Definição de Pronto (DoD)**: Diagramas de atividades aprovados e publicados na documentação.
- **Observações Técnicas**: Essencial para a apresentação final aos professores do curso.

---

### [DOC-007] Elaborar Diagrama de Arquitetura em Camadas e Visão de Containers C4
- **ID**: `DOC-007`
- **Título**: Elaborar Diagrama de Arquitetura em Camadas e Visão de Containers C4
- **Área**: Documentação
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 2 (S2)
- **Sequência na Squad**: ⬅️ Anterior: `DOC-006` | ➡️ Próximo: `DOC-008`
- **Dependências Diretas**: `DOC-001`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: documentacao
- **Objetivo**: Representar a arquitetura técnica da solução em múltiplos níveis de abstração segundo o modelo C4.
- **Descrição**: Criar docs/diagramas/arquitetura-c4.md contendo: Diagrama de Contexto de Sistema (nível 1), Diagrama de Containers (nível 2: SPA React, API Fastify, Banco Postgres, Docker) e Diagrama de Componentes (nível 3: Controllers, Services, Repositories).
- **História de Usuário**: Como Arquiteto de Software, quero o modelo C4 documentado, para demonstrar como os subsistemas se comunicam com segurança.
- **Critérios de Aceitação**:
- Diagramas C4 Context e Container renderizados em Mermaid ou imagem.
- Protocolos e portas de comunicação documentados (HTTPS, TCP 5432, REST JSON).
- Detalhamento dos limites de segurança e autenticação JWT.
- **Definição de Pronto (DoD)**: Documento de arquitetura C4 publicado e revisado.
- **Observações Técnicas**: Adotar a notação padronizada de Simon Brown para o modelo C4.

---

### [DOC-008] Elaborar Diagrama Entidade-Relacionamento (DER) Oficial do Banco de Dados
- **ID**: `DOC-008`
- **Título**: Elaborar Diagrama Entidade-Relacionamento (DER) Oficial do Banco de Dados
- **Área**: Documentação
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 2 (S2)
- **Sequência na Squad**: ⬅️ Anterior: `DOC-007` | ➡️ Próximo: `DOC-009`
- **Dependências Diretas**: `DOC-002`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: documentacao
- **Objetivo**: Documentar graficamente o modelo de dados relacional completo implementado no PostgreSQL.
- **Descrição**: Gerar e documentar em docs/banco/der-oficial.md o diagrama DER contendo todas as tabelas (users, profiles, courses, classes, enrollments, learning_modules, competencies, attendance, tasks, grades, etc.), chaves primárias, estrangeiras e cardinalidades.
- **História de Usuário**: Como Desenvolvedor de Banco, quero ter o DER atualizado, para consultar os relacionamentos e montar queries e views analíticas complexas.
- **Critérios de Aceitação**:
- Diagrama legível cobrindo todas as entidades do sistema.
- Chaves PK e FK explicitamente indicadas com cardinalidades corretas.
- Exportado em Mermaid ou diagrama gráfico de alta resolução.
- **Definição de Pronto (DoD)**: DER oficial integrado à documentação de banco de dados.
- **Observações Técnicas**: Pode ser gerado com auxílio de prisma-erd-generator.

---

### [DOC-009] Construir Dicionário de Dados Completo com Tipos, Chaves e Restrições
- **ID**: `DOC-009`
- **Título**: Construir Dicionário de Dados Completo com Tipos, Chaves e Restrições
- **Área**: Documentação
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 2 (S2)
- **Sequência na Squad**: ⬅️ Anterior: `DOC-008` | ➡️ Próximo: `DOC-010`
- **Dependências Diretas**: `DOC-008`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: documentacao
- **Objetivo**: Descrever detalhadamente cada tabela, coluna, tipo de dado e regra de validação do banco.
- **Descrição**: Criar docs/banco/dicionario-dados.md com tabelas estruturadas contendo: Nome da Tabela, Nome da Coluna, Tipo SQL, Nulo/Não Nulo, Chave (PK/FK), Default e Descrição semântica de negócio para cada campo.
- **História de Usuário**: Como Engenheiro de Dados, quero consultar o dicionário de dados, para entender o significado e restrições de cada coluna sem adivinhações.
- **Critérios de Aceitação**:
- Todas as tabelas do Lote 1 e 2 descritas exaustivamente.
- Constraints de integridade (CHECK, UNIQUE) explicadas em português.
- Dicionário alinhado 100% com o schema.prisma.
- **Definição de Pronto (DoD)**: Dicionário de dados aprovado e disponível para consulta da equipe.
- **Observações Técnicas**: Manter atualizado a cada migration nova adicionada ao Prisma.

---

### [DOC-010] Elaborar Manual de Instalação, Configuração Local e Docker
- **ID**: `DOC-010`
- **Título**: Elaborar Manual de Instalação, Configuração Local e Docker
- **Área**: Documentação
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 2 (S2)
- **Sequência na Squad**: ⬅️ Anterior: `DOC-009` | ➡️ Próximo: `DOC-011`
- **Dependências Diretas**: `DOC-001, DB-003, BE-001, FE-001`
- **Prioridade**: P0 | **Estimativa**: 2 SP | **Tipo**: documentacao
- **Objetivo**: Instruir qualquer novo integrante da equipe ou avaliador a clonar, configurar e rodar o projeto do zero sem erros.
- **Descrição**: Criar docs/infra/setup-local.md com roteiro passo a passo: pré-requisitos (Node.js 20+, Docker Desktop, Git), clonagem do repositório, configuração do .env a partir do .env.example, inicialização do banco via docker compose, execução de migrations, carga de seeds e comandos npm run dev para front e back.
- **História de Usuário**: Como Novo Integrante da Equipe, quero seguir um manual de setup claro, para rodar o sistema localmente em menos de 10 minutos.
- **Critérios de Aceitação**:
- Testado em máquina limpa seguindo estritamente as instruções sem erros.
- Guia de resolução de problemas comuns (portas em conflito, erro de conexão com banco).
- Rastreabilidade de scripts do package.json.
- **Definição de Pronto (DoD)**: Manual publicado e validado por outro membro do time.
- **Observações Técnicas**: Garantir comandos compatíveis tanto com Windows (PowerShell) quanto Linux/macOS.

---

### [DOC-011] Elaborar README.md Principal do Repositório com Badges e Guia Rápido
- **ID**: `DOC-011`
- **Título**: Elaborar README.md Principal do Repositório com Badges e Guia Rápido
- **Área**: Documentação
- **Epic**: EPIC-10: Relatórios, Governança de Dados & Qualidade
- **Lote / Sprint**: Lote 3 (S3)
- **Sequência na Squad**: ⬅️ Anterior: `DOC-010` | ➡️ Próximo: `DOC-012`
- **Dependências Diretas**: `DOC-001, DOC-007, DOC-010`
- **Prioridade**: P0 | **Estimativa**: 2 SP | **Tipo**: documentacao
- **Objetivo**: Estruturar o README.md principal na raiz do repositório como porta de entrada clara, profissional e acadêmica do projeto NEXA.
- **Descrição**: Atualizar README.md (em UTF-8 padrão) contendo: visão executiva do Sistema de Monitoramento Acadêmico SENAI, arquitetura técnica, links para os 5 GitHub Projects, instruções rápidas de execução (Quick Start), estrutura de pastas, fluxo GitFlow e convenção de commits.
- **História de Usuário**: Como Professor Orientador ou Desenvolvedor, quero abrir o repositório no GitHub e compreender imediatamente a arquitetura e como executar o projeto.
- **Critérios de Aceitação**:
- Codificação UTF-8 limpa e renderização perfeita no GitHub.
- Links diretos para a documentação detalhada em docs/ e para os 5 quadros do GitHub Projects.
- Seção de padrões de branch (main, develop, feature/*, bugfix/*) e Conventional Commits.
- **Definição de Pronto (DoD)**: README.md principal revisado e publicado na raiz do repositório.
- **Observações Técnicas**: Evita duplicação apontando para os manuais específicos em docs/.

---

### [DOC-012] Criar Guia de Variáveis de Ambiente e Segurança (.env.example)
- **ID**: `DOC-012`
- **Título**: Criar Guia de Variáveis de Ambiente e Segurança (.env.example)
- **Área**: Documentação
- **Epic**: EPIC-01: Autenticação, Perfis (RBAC) & Segurança
- **Lote / Sprint**: Lote 3 (S3)
- **Sequência na Squad**: ⬅️ Anterior: `DOC-011` | ➡️ Próximo: `DOC-013`
- **Dependências Diretas**: `DOC-010, DB-003, BE-005, FE-010`
- **Prioridade**: P0 | **Estimativa**: 1 SP | **Tipo**: documentacao
- **Objetivo**: Documentar todas as variáveis de ambiente necessárias para Front-end, Back-end e Banco de Dados, orientando sobre geração e proteção de segredos.
- **Descrição**: Elaborar docs/infra/guia-variaveis-ambiente.md detalhando: DATABASE_URL, JWT_ACCESS_SECRET, JWT_REFRESH_SECRET, COOKIE_SECRET, CORS_ORIGIN, VITE_API_URL e GITHUB_TOKEN, com instruções de geração de chaves criptográficas seguras (openssl rand -hex 32) e boas práticas de não versionamento.
- **História de Usuário**: Como Desenvolvedor da Equipe, quero saber exatamente o propósito e o formato de cada variável do .env sem expor segredos no Git.
- **Critérios de Aceitação**:
- Tabela explicando cada variável, valor padrão de desenvolvimento e obrigatoriedade em produção.
- Sincronizado com .env.example da raiz, backend e frontend.
- Orientações de rotação de segredos em caso de exposição.
- **Definição de Pronto (DoD)**: Guia de variáveis de ambiente publicado e validado.
- **Observações Técnicas**: Cumpre o requisito de segurança e proteção de credenciais (seção 10 e seção 14).

---

### [DOC-013] Documentar Especificação de API REST com OpenAPI / Swagger
- **ID**: `DOC-013`
- **Título**: Documentar Especificação de API REST com OpenAPI / Swagger
- **Área**: Documentação
- **Epic**: EPIC-10: Relatórios, Governança de Dados & Qualidade
- **Lote / Sprint**: Lote 3 (S3)
- **Sequência na Squad**: ⬅️ Anterior: `DOC-012` | ➡️ Próximo: `DOC-014`
- **Dependências Diretas**: `DOC-002, BE-020, BE-030, BE-050`
- **Prioridade**: P0 | **Estimativa**: 3 SP | **Tipo**: documentacao
- **Objetivo**: Consolidar a referência completa de contratos de endpoints REST (métodos, rotas, payloads, respostas, códigos HTTP e regras RBAC).
- **Descrição**: Criar docs/api/especificacao-api-openapi.md e sincronizar docs/api/openapi-spec.json cobrindo todos os endpoints de BE-005 a BE-049, incluindo exemplos de requisição/resposta, códigos de erro padronizados (400, 401, 403, 404, 409, 422) e matriz de permissões por papel.
- **História de Usuário**: Como Desenvolvedor Front-end ou Avaliador Técnico, quero consultar o catálogo completo de endpoints e seus contratos de dados.
- **Critérios de Aceitação**:
- Todos os endpoints documentados com Método HTTP, Caminho, Objetivo, Corpo, Resposta, Status e Autorização.
- Matriz resumida de permissões RBAC (ADMIN, COORDINATOR, TEACHER, STUDENT) por rota.
- Alinhado com a rota interativa /docs (BE-050).
- **Definição de Pronto (DoD)**: Especificação de API publicada e validada entre as squads de Front-end e Back-end.
- **Observações Técnicas**: Garante que Front-end e Back-end trabalhem sempre com contratos 100% compatíveis.

---

### [DOC-014] Elaborar Manual de Usabilidade do Professor e Diário Eletrônico
- **ID**: `DOC-014`
- **Título**: Elaborar Manual de Usabilidade do Professor e Diário Eletrônico
- **Área**: Documentação
- **Epic**: EPIC-05: Dashboard Híbrido do Professor & Visão 360°
- **Lote / Sprint**: Lote 4 (S4)
- **Sequência na Squad**: ⬅️ Anterior: `DOC-013` | ➡️ Próximo: `DOC-015`
- **Dependências Diretas**: `DOC-003, FE-022, FE-025, FE-031, FE-034, FE-045`
- **Prioridade**: P1 | **Estimativa**: 5 SP | **Tipo**: documentacao
- **Objetivo**: Criar guia prático ilustrado orientando professores e coordenadores no uso diário da plataforma NEXA.
- **Descrição**: Redigir docs/manuais/manual-professor.md cobrindo passo a passo: como registrar aula, como fazer chamada rápida em 1 clique, como avaliar peças práticas por rubricas na oficina, como interpretar alertas explicáveis de risco, como usar a Ficha 360° e como responder pedidos de ajuda confidenciais.
- **História de Usuário**: Como Professor SENAI, quero um manual direto ao ponto para utilizar o diário rápido, avaliar oficinas e apoiar meus alunos com segurança.
- **Critérios de Aceitação**:
- Roteiros passo a passo para cada fluxo docente (FE-021 a FE-034, FE-042, FE-045, FE-046, FE-048).
- Seção ética explicando como interpretar diagnósticos e alertas como apoio pedagógico.
- Linguagem clara, objetiva e acessível.
- **Definição de Pronto (DoD)**: Manual do professor revisado e pronto para entrega acadêmica.
- **Observações Técnicas**: Atende ao entregável de Manual do Usuário (seção 10).

---

### [DOC-015] Elaborar Manual de Usabilidade do Aluno (Portal e Autoavaliação)
- **ID**: `DOC-015`
- **Título**: Elaborar Manual de Usabilidade do Aluno (Portal e Autoavaliação)
- **Área**: Documentação
- **Epic**: EPIC-06: Portal de Autonomia do Aluno & Pendências
- **Lote / Sprint**: Lote 4 (S4)
- **Sequência na Squad**: ⬅️ Anterior: `DOC-014` | ➡️ Próximo: `DOC-016`
- **Dependências Diretas**: `DOC-003, FE-035, FE-036, FE-041, FE-044, FE-047`
- **Prioridade**: P1 | **Estimativa**: 3 SP | **Tipo**: documentacao
- **Objetivo**: Criar guia prático para os estudantes utilizarem o Portal de Autonomia, acompanharem pendências, realizarem autoavaliações e solicitarem mentoria.
- **Descrição**: Redigir docs/manuais/manual-aluno.md explicando: consulta de notas e limite de 75% de presença, painel de atividades práticas pendentes/atrasadas, como preencher a autoavaliação de competências com sinceridade, como funciona a confidencialidade dos pedidos de ajuda e como desbloquear conquistas (badges).
- **História de Usuário**: Como Estudante SENAI, quero entender como acompanhar meu progresso, avaliar minhas habilidades práticas e pedir ajuda sem receio de exposição.
- **Critérios de Aceitação**:
- Cobre todas as funcionalidades do Portal do Aluno (FE-035 a FE-041, FE-044, FE-047).
- Explica de forma transparente as regras de pontuação e níveis de habilidade.
- Destaca as garantias de privacidade do estudante.
- **Definição de Pronto (DoD)**: Manual do aluno revisado e publicado em docs/manuais/.
- **Observações Técnicas**: Complementa o Manual do Usuário (DOC-014).

---

### [DOC-016] Elaborar Plano Estratégico de Testes e Relatório de Qualidade
- **ID**: `DOC-016`
- **Título**: Elaborar Plano Estratégico de Testes e Relatório de Qualidade
- **Área**: Documentação
- **Epic**: EPIC-10: Relatórios, Governança de Dados & Qualidade
- **Lote / Sprint**: Lote 4 (S4)
- **Sequência na Squad**: ⬅️ Anterior: `DOC-015` | ➡️ Próximo: `DOC-017`
- **Dependências Diretas**: `DOC-002, DB-050, BE-020, BE-030, BE-040, FE-030, FE-050`
- **Prioridade**: P1 | **Estimativa**: 3 SP | **Tipo**: documentacao
- **Objetivo**: Documentar a estratégia de testes (unitários, integração, integridade de banco e E2E) e consolidar o relatório de resultados e evidências.
- **Descrição**: Criar docs/qualidade/plano-e-relatorio-testes.md contendo: escopo de testes por camada (DB-010, DB-050, BE-020, BE-030, BE-040, FE-030, FE-050), matriz de casos de teste para os requisitos críticos, testes de segurança/autorização (RBAC e prevenção de IDOR) e checklist de validação de aceite.
- **História de Usuário**: Como Avaliador de Engenharia de Software, quero verificar o plano de testes e os resultados obtidos em cada camada da aplicação.
- **Critérios de Aceitação**:
- Mapeia casos de teste positivos, negativos e de segurança (acesso não autorizado 401/403).
- Inclui roteiro de execução reproduzível dos testes automatizados.
- Registra evidências de validação dos fluxos de ponta a ponta.
- **Definição de Pronto (DoD)**: Plano e relatório de testes concluídos e alinhados com as suítes automatizadas.
- **Observações Técnicas**: Cobre os entregáveis: Plano de testes, Relatório de testes e Evidências (seção 10).

---

### [DOC-017] Elaborar Relatório de Conformidade LGPD, Segurança e Plano de Backup
- **ID**: `DOC-017`
- **Título**: Elaborar Relatório de Conformidade LGPD, Segurança e Plano de Backup
- **Área**: Documentação
- **Epic**: EPIC-10: Relatórios, Governança de Dados & Qualidade
- **Lote / Sprint**: Lote 5 (S5)
- **Sequência na Squad**: ⬅️ Anterior: `DOC-016` | ➡️ Próximo: `DOC-018`
- **Dependências Diretas**: `DOC-002, DB-009, DB-043, DB-048, DB-049, BE-045, BE-048`
- **Prioridade**: P1 | **Estimativa**: 3 SP | **Tipo**: documentacao
- **Objetivo**: Documentar todas as medidas técnicas e organizacionais de proteção de dados pessoais (LGPD), controle de acesso, retenção e recuperação de desastres.
- **Descrição**: Criar docs/governanca/seguranca-lgpd-backup.md detalhando: princípio do menor privilégio (RBAC), isolamento de dados entre alunos, proteção de pedidos de ajuda confidenciais e observações pedagógicas restritas, hash Argon2/Bcrypt, auditoria (audit_logs), rotina de anonimização (DB-049) e procedimento de backup/restauração (DB-048).
- **História de Usuário**: Como Coordenador e Banca Avaliadora, quero comprovação documentada de que o sistema respeita a LGPD e protege os dados acadêmicos dos estudantes.
- **Critérios de Aceitação**:
- Mapeia cada requisito da seção 14 (Segurança, privacidade e responsabilidade) para sua implementação técnica.
- Documenta o RPO/RTO e o passo a passo de backup e restore (DB-048).
- Explicita a diretriz ética dos alertas e diagnósticos explicáveis.
- **Definição de Pronto (DoD)**: Documento de Segurança, LGPD e Plano de Backup publicado e revisado.
- **Observações Técnicas**: Une Análise de Segurança/Privacidade e Plano de Backup/Recuperação em um entregável coeso.

---

### [DOC-018] Documentar Registro de Decisões de Arquitetura (ADRs) e Guia de Deploy
- **ID**: `DOC-018`
- **Título**: Documentar Registro de Decisões de Arquitetura (ADRs) e Guia de Deploy
- **Área**: Documentação
- **Epic**: EPIC-10: Relatórios, Governança de Dados & Qualidade
- **Lote / Sprint**: Lote 5 (S5)
- **Sequência na Squad**: ⬅️ Anterior: `DOC-017` | ➡️ Próximo: `DOC-019`
- **Dependências Diretas**: `DOC-007, DOC-010, DOC-012, DB-050, BE-050, FE-050`
- **Prioridade**: P1 | **Estimativa**: 2 SP | **Tipo**: documentacao
- **Objetivo**: Registrar formalmente as decisões arquiteturais do projeto (ADRs) e o guia de publicação (Deploy) em ambiente de produção/homologação.
- **Descrição**: Criar docs/arquitetura/adrs-e-deploy.md contendo: ADR-001 (Escolha de React 19 + Tailwind v4), ADR-002 (Node.js + Fastify + Zod em camadas), ADR-003 (PostgreSQL 16 + Prisma ORM e Views Analíticas), ADR-004 (Autenticação JWT + HttpOnly Refresh Rotation) e ADR-005 (Motor de Diagnóstico Explicável Baseado em Regras vs IA Caixa-Preta), além do passo a passo de deploy.
- **História de Usuário**: Como Arquiteto de Software e Banca Avaliadora, quero entender as justificativas técnicas por trás de cada escolha tecnológica e como publicar a aplicação.
- **Critérios de Aceitação**:
- Cada ADR segue o formato Contexto -> Decisão -> Consequências Positivas e Limitações.
- Guia de deploy detalhando build de produção do Front-end, Back-end e banco PostgreSQL.
- Instruções de configuração de HTTPS, CORS e variáveis seguras em produção.
- **Definição de Pronto (DoD)**: ADRs e Guia de Deploy publicados em docs/arquitetura/.
- **Observações Técnicas**: Cobre Registro das decisões arquiteturais e Documentação de deploy (seção 10).

---

### [DOC-019] Preparar Slides, Roteiro de Demonstração e Pitch da Banca Final SENAI
- **ID**: `DOC-019`
- **Título**: Preparar Slides, Roteiro de Demonstração e Pitch da Banca Final SENAI
- **Área**: Documentação
- **Epic**: EPIC-10: Relatórios, Governança de Dados & Qualidade
- **Lote / Sprint**: Lote 5 (S5)
- **Sequência na Squad**: ⬅️ Anterior: `DOC-018` | ➡️ Próximo: `DOC-020`
- **Dependências Diretas**: `DOC-001, DOC-014, DOC-015, DOC-016, FE-050, BE-050, DB-050`
- **Prioridade**: P0 | **Estimativa**: 5 SP | **Tipo**: documentacao
- **Objetivo**: Estruturar a apresentação executiva e o roteiro de demonstração ao vivo (Live Demo) para a banca avaliadora do semestre.
- **Descrição**: Criar docs/apresentacao/roteiro-banca-final.md contendo: estrutura slide a slide (Problema, Solução NEXA, Arquitetura, Diferenciais Pedagógicos SENAI, Demonstração Guiada nos Perfis Professor/Aluno/Coordenador, Métricas de Qualidade e Conclusão) e script de demonstração de 10 minutos sem falhas.
- **História de Usuário**: Como Equipe de Estudantes de ADS, queremos um roteiro de apresentação impecável que demonstre todo o valor construído nos 170 cards do projeto.
- **Critérios de Aceitação**:
- Roteiro cronometrado cobrindo o fluxo completo de ponta a ponta.
- Destaca os 4 pilares da pesquisa com usuários (Dashboard Híbrido, Portal de Autonomia, Autoavaliação/Diagnóstico Explicável e Canal Confidencial).
- Lista de perguntas frequentes da banca (FAQ técnico) com respostas preparadas.
- **Definição de Pronto (DoD)**: Apresentação e roteiro de Live Demo prontos e ensaiados pela equipe.
- **Observações Técnicas**: Atende ao entregável de Preparação da apresentação final (seção 10).

---

### [DOC-020] Redigir Relatório Final Consolidado do Projeto de Conclusão de Semestre
- **ID**: `DOC-020`
- **Título**: Redigir Relatório Final Consolidado do Projeto de Conclusão de Semestre
- **Área**: Documentação
- **Epic**: EPIC-10: Relatórios, Governança de Dados & Qualidade
- **Lote / Sprint**: Lote 5 (S5)
- **Sequência na Squad**: ⬅️ Anterior: `DOC-019` | ➡️ Próximo: `Marco Final Concluído (100%)`
- **Dependências Diretas**: `DOC-001, DOC-005, DOC-008, DOC-009, DOC-013, DOC-016, DOC-017, DOC-018, DOC-019, DB-050, BE-050, FE-050`
- **Prioridade**: P0 | **Estimativa**: 8 SP | **Tipo**: documentacao
- **Objetivo**: Consolidar o documento acadêmico e técnico mestre do Projeto NEXA, unificando todos os entregáveis, matriz de rastreabilidade e validação final dos 170 cards.
- **Descrição**: Elaborar docs/academico/relatorio-final-nexa.md reunindo: resumo executivo, arquitetura e stack validada, mapa de épicos, matriz de dependências cruzadas entre Front-end (FE-001 a FE-050), Back-end (BE-001 a BE-050), Banco de Dados (DB-001 a DB-050) e Documentação (DOC-001 a DOC-020), resultados dos testes, conformidade LGPD e conclusão semestral.
- **História de Usuário**: Como Professor Orientador e Coordenação do Curso de ADS, queremos o Relatório Final completo comprovando a entrega funcional, documentada e integrada do sistema.
- **Critérios de Aceitação**:
- Consolida referências para todos os documentos produzidos de DOC-001 a DOC-019.
- Inclui matriz de rastreabilidade completa dos 170 cards (50 FE + 50 BE + 50 DB + 20 DOC).
- Checklist de validação final 100% verificado e aprovado.
- **Definição de Pronto (DoD)**: Projeto NEXA 100% documentado, revisado e entregue para avaliação final do semestre.
- **Observações Técnicas**: Marco de encerramento geral (Card 170/170) de todo o backlog do projeto.

