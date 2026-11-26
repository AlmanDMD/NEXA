# Roteiro de Apresentação — NEXA
**Sistema de Monitoramento do Desempenho Acadêmico**  
**Curso:** Tecnologia em Análise e Desenvolvimento de Sistemas (TADS) — **SENAI Gaspar Ricardo Junior (2026)**  
**Integrantes:** Ahslam Mendes, Letícia Vieira, Matheus Boff e Nicolas Pureza

> Todas as falas abaixo também estão embutidas nas **Notas do Apresentador (Speaker Notes)** dentro do arquivo `NEXA_Apresentacao.pptx`.

---

## Integrante 1 — Ahslam Mendes (Apresentação do Projeto)

### Slide 1 — Capa
**Fala sugerida:**  
Boa tarde a todos! Nós somos alunos do curso de Análise e Desenvolvimento de Sistemas do SENAI, e hoje vamos apresentar o **NEXA** — nosso Sistema de Monitoramento do Desempenho Acadêmico.  
O grupo é formado por mim, Ahslam Mendes, pela Letícia Vieira, pelo Matheus Boff e pelo Nicolas Pureza.  
Nós dividimos a apresentação em quatro partes: eu começo explicando o problema e o que é o NEXA; em seguida, a Letícia apresenta os objetivos e o Frontend; depois o Matheus detalha a parte técnica principal do Backend; e o Nicolas fecha com o Banco de Dados, a integração completa do sistema e os benefícios finais.

### Slide 2 — Qual é o problema?
**Fala sugerida:**  
Para entender por que criamos o NEXA, precisamos olhar para um problema muito comum nas instituições de ensino, especialmente em cursos técnicos e práticos.  
Hoje, a maioria dos sistemas acadêmicos funciona apenas como um arquivo: eles guardam a nota final e o total de faltas. Mas eles não ajudam o professor a enxergar o desempenho do aluno de forma integrada durante o processo.  
Isso gera quatro dificuldades claras: primeiro, o diagnóstico tardio — muitas vezes a coordenação e o professor só percebem que o aluno está com dificuldade no fim do módulo, quando ele já reprovou. Segundo, falta uma visualização clara da evolução ao longo das semanas. Terceiro, muitos alunos têm receio de tirar dúvidas em público na oficina ou no laboratório. E quarto, os professores acabam sobrecarregados tentando controlar tudo em planilhas separadas.  
Foi exatamente para resolver esse cenário que nasceu o NEXA.

### Slide 3 — O que é o NEXA?
**Fala sugerida:**  
Então, o que é o NEXA? Ele é uma plataforma web de acompanhamento e inteligência pedagógica pensada especialmente para a formação profissional técnica.  
A proposta principal do NEXA é simples: em vez de deixar notas, faltas e observações espalhadas, ele centraliza tudo em um só lugar. E além das notas tradicionais, ele também considera a avaliação prática por rubricas e a autoavaliação do próprio estudante.  
Como vocês podem ver no esquema à direita, o sistema cruza essas informações — frequência, notas e autoavaliação — para gerar uma visão clara para professores e coordenação. Quando um aluno começa a faltar ou cai de rendimento, o NEXA gera alertas explicáveis, mostrando o motivo real. Tudo isso respeitando a privacidade dos dados.  
Agora, passo a palavra para a Letícia, que vai explicar para que o projeto serve na prática e mostrar como é a interface do sistema.

---

## Integrante 2 — Letícia Vieira (Objetivos e Frontend)

### Slide 4 — Para que o projeto vai servir?
**Fala sugerida:**  
Obrigada, Ahslam! Falando agora sobre a finalidade prática do projeto: para que o NEXA vai servir no dia a dia da escola?  
Nós resumimos em cinco objetivos principais. Primeiro, monitorar o desempenho dos estudantes de forma contínua, não só no fechamento do bimestre. Segundo, identificar dificuldades acadêmicas cedo, antes que o aluno perca o módulo. Terceiro, acompanhar a evolução individual, permitindo inclusive cruzar o que o aluno acha que sabe com a avaliação do professor.  
Além disso, o NEXA facilita muito a rotina do professor, eliminando controles manuais em planilhas, e dá à equipe pedagógica base concreta para tomar decisões — como chamar um aluno para reforço ou mentoria na hora certa.

### Slide 5 — Frontend: Interface do sistema
**Fala sugerida:**  
Para entregar esses objetivos, o usuário precisa de uma interface clara. É aí que entra o Frontend — que é toda a parte visual do sistema, construída com React, TypeScript e Tailwind CSS, com a qual professores, alunos e coordenação interagem diretamente no navegador.  
Organizamos a navegação em telas objetivas: uma tela de Login segura, um Dashboard com a visão geral da turma, a Lista de Alunos com indicadores de status, o Perfil do Aluno com seu histórico detalhado e uma área de Relatórios.  
Aqui à direita temos uma prévia visual de como essas informações são organizadas. E um ponto fundamental do nosso Frontend é a usabilidade e a responsividade: como muitos professores usam o sistema em oficinas e laboratórios, a tela precisa funcionar bem tanto no computador quanto no celular ou tablet.

### Slide 6 — Funcionalidades e experiência do usuário
**Fala sugerida:**  
Na experiência do usuário, o foco do NEXA é transformar dados em informação fácil de ler.  
O professor e o aluno conseguem consultar notas e frequência sem precisar abrir várias telas. Como mostra a ilustração à direita, o sistema exibe gráficos de evolução acadêmica que comparam o desempenho observado com a autoavaliação do estudante, além de monitorar a frequência antes de atingir o limite mínimo de 75%.  
Quando há algum risco — como atividades práticas pendentes ou queda de rendimento — o sistema destaca esse estudante com um alerta explicável, dizendo exatamente o porquê. A navegação é simples e cada perfil enxerga as informações adequadas ao seu papel.  
Agora passo a palavra para o Matheus, que vai explicar como o Backend faz toda essa inteligência funcionar por trás das telas.

---

## Integrante 3 — Matheus Boff (Backend — Parte Técnica Principal)

### Slide 7 — Backend: Como o sistema funciona por trás?
**Fala sugerida:**  
Obrigado, Letícia! Agora vamos olhar por baixo do capô do NEXA, entrando no Backend — que é o cérebro do sistema.  
Enquanto o Frontend cuida da parte visual, o Backend roda no servidor, desenvolvido em Python com o framework FastAPI. É ele quem guarda toda a lógica de funcionamento, as validações e a segurança das operações.  
Sempre que um professor lança uma nota ou consulta um gráfico na tela, o Frontend envia uma solicitação pela internet usando uma API REST — que é um padrão de comunicação via HTTP com dados em formato JSON. O Backend recebe esse pedido, verifica se o usuário está autenticado com segurança, processa as regras e devolve uma resposta organizada para a tela exibir.

### Slide 8 — Arquitetura e organização do Backend
**Fala sugerida:**  
Para que o Backend não vire um código confuso conforme o projeto cresce, nós adotamos uma arquitetura em camadas desacopladas. No nosso repositório em FastAPI, cada camada tem uma responsabilidade bem definida:  
1. O **Controller** (nossas pastas de `routers`) é a porta de entrada: ele recebe a requisição do Frontend e direciona o pedido.  
2. O **DTO** (nossos `schemas` com Pydantic) funciona como um pacote padronizado e validado que transporta os dados com segurança entre as camadas.  
3. O **Service** é onde moram as regras de negócio — por exemplo, calcular médias e detectar alertas.  
4. O **Repository** é o responsável por conversar com o banco de dados, buscando ou salvando informações.  
5. E a **Entity** (nossos `models`) representa a estrutura das tabelas do banco dentro do código.  

O grande ganho dessa organização é a manutenção: se amanhã precisarmos mudar uma fórmula de alerta, mexemos só no Service, sem afetar o restante do sistema.

### Slide 9 — Regras de negócio e processamento
**Fala sugerida:**  
E o que o Backend faz na prática com os dados do aluno? Ele segue um fluxo bem definido de quatro etapas.  
Primeiro, ao receber uma nota, rubrica prática ou chamada, o Backend valida tudo para garantir que não haja dados inválidos ou alterações fora do prazo. Segundo, ele organiza esses dados e calcula os indicadores de desempenho e o percentual de presença por módulo.  
Terceiro, entra a inteligência: o sistema identifica situações de atenção, como quando a frequência se aproxima do limite mínimo de 75% ou quando há uma grande diferença entre a autoavaliação do aluno e a nota do professor. Por fim, ele disponibiliza tudo para o Frontend de forma segura — respeitando o controle de acesso por perfil, protegendo observações sensíveis com criptografia e registrando auditoria.  
Agora o Nicolas assume para mostrar onde tudo isso fica guardado no Banco de Dados e como as três camadas se conectam.

---

## Integrante 4 — Nicolas Pureza (Banco de Dados e Conclusão)

### Slide 10 — Banco de Dados: Onde as informações ficam armazenadas?
**Fala sugerida:**  
Obrigado, Matheus! Agora chegamos à base de tudo: o Banco de Dados, que é onde todas as informações do NEXA ficam armazenadas com segurança e organização.  
Nós utilizamos o PostgreSQL 16 rodando em contêiner Docker, com modelagem relacional até a Terceira Forma Normal — o que evita dados repetidos e garante que as informações nunca fiquem inconsistentes.  
Aqui à direita temos o nosso Diagrama Entidade-Relacionamento simplificado. Podemos ver as entidades principais: Turmas, Disciplinas, Professores, Alunos, Notas e Frequências. Os relacionamentos conectam tudo de forma lógica: uma Turma tem vários Alunos; os Professores ministram Disciplinas; e cada Aluno acumula seus registros de Notas e Frequências vinculados às suas Disciplinas. Além disso, o banco conta com tabelas de usuários, sessões e trilha de auditoria alinhada à LGPD.

### Slide 11 — Integração entre Frontend, Backend e Banco de Dados
**Fala sugerida:**  
Para fechar a parte técnica, este fluxograma mostra como as três camadas trabalham juntas em qualquer ação no NEXA, em 7 passos simples:  
1. Primeiro, o usuário — aluno ou professor — acessa o Frontend no navegador.  
2. Ao clicar para consultar um desempenho ou lançar uma nota, o Frontend envia uma requisição ao Backend.  
3. O Backend recebe, autentica e processa as regras de negócio.  
4. Em seguida, o Backend consulta ou atualiza o Banco de Dados.  
5. O Banco de Dados processa a operação e retorna as informações solicitadas.  
6. O Backend formata e envia a resposta segura de volta ao Frontend.  
7. E por fim, o usuário visualiza os resultados atualizados na tela.  

Essa integração bem dividida é o que garante que o NEXA seja rápido, confiável e fácil de manter.

### Slide 12 — Benefícios e considerações finais
**Fala sugerida:**  
Para concluir, o NEXA traz benefícios diretos para toda a comunidade acadêmica: melhora o acompanhamento contínuo dos alunos, permite identificar dificuldades de forma antecipada, centraliza e protege as informações escolares, e dá aos professores e à coordenação apoio real para tomar decisões pedagógicas.  
Com isso, o sistema contribui diretamente para reduzir reprovações e evitar a evasão escolar — unindo organização de dados, desenvolvimento em camadas e foco humano no estudante.  
Em nome do grupo — Ahslam, Letícia, Matheus e eu, Nicolas — agradecemos a atenção de todos e ficamos à disposição para perguntas!
