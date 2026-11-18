export const academicDashboard = {
  totalStudents: 154,
  overallAverage: 7.6,
  averageAttendance: 89.4,
  attentionStudents: 18,
  criticalStudents: 5,
  studentsAdded: 8,
  averageChange: 0.3,
  attendanceChange: 1.8,
  monthlyAverages: [
    { month: 'Jan', average: 6.0, target: 5.8 },
    { month: 'Fev', average: 6.2, target: 5.9 },
    { month: 'Mar', average: 6.1, target: 5.9 },
    { month: 'Abr', average: 6.6, target: 6.0 },
    { month: 'Mai', average: 7.1, target: 6.2 },
    { month: 'Jun', average: 7.6, target: 6.5 },
  ],
  monthlyAttendance: [
    { month: 'Jan', average: 87.6, target: 85 },
    { month: 'Fev', average: 88.1, target: 85 },
    { month: 'Mar', average: 87.8, target: 85 },
    { month: 'Abr', average: 88.5, target: 85 },
    { month: 'Mai', average: 89.0, target: 85 },
    { month: 'Jun', average: 89.4, target: 85 },
  ],
  performanceDistribution: [
    { label: '8,0 a 10,0', count: 74, percentage: 48 },
    { label: '6,0 a 7,9', count: 45, percentage: 29 },
    { label: '4,0 a 5,9', count: 25, percentage: 16 },
    { label: 'Abaixo de 4,0', count: 10, percentage: 7 },
  ],
  attendanceDistribution: [
    { label: '90% a 100%', count: 73, percentage: 47 },
    { label: '75% a 89%', count: 69, percentage: 45 },
    { label: 'Abaixo de 75%', count: 12, percentage: 8 },
  ],
};

export const academicStudents = [
  { id: 's-01', name: 'Ana Luísa Ribeiro', registration: '2024.0187', className: 'Eletrotécnica 2A', course: 'Técnico em Eletrotécnica', average: 8.7, attendance: 96, status: 'Regular', updatedAt: 'Hoje, 08:42' },
  { id: 's-02', name: 'Bruno Henrique Alves', registration: '2024.0214', className: 'Mecânica 1B', course: 'Técnico em Mecânica', average: 6.1, attendance: 82, status: 'Atenção', updatedAt: 'Hoje, 08:15' },
  { id: 's-03', name: 'Camila Ferreira Dias', registration: '2023.0098', className: 'Administração 3A', course: 'Técnico em Administração', average: 9.1, attendance: 98, status: 'Regular', updatedAt: 'Ontem, 16:20' },
  { id: 's-04', name: 'Daniel Souza Martins', registration: '2024.0302', className: 'Informática 1A', course: 'Técnico em Informática', average: 5.4, attendance: 74, status: 'Crítico', updatedAt: 'Ontem, 15:48' },
  { id: 's-05', name: 'Elisa Nogueira Costa', registration: '2024.0165', className: 'Eletrotécnica 2A', course: 'Técnico em Eletrotécnica', average: 7.9, attendance: 91, status: 'Regular', updatedAt: '12 jun, 14:32' },
  { id: 's-06', name: 'Felipe Andrade Lima', registration: '2024.0241', className: 'Mecânica 1B', course: 'Técnico em Mecânica', average: 6.8, attendance: 87, status: 'Atenção', updatedAt: '12 jun, 11:06' },
  { id: 's-07', name: 'Giovana Martins Reis', registration: '2023.0159', className: 'Administração 3A', course: 'Técnico em Administração', average: 8.2, attendance: 94, status: 'Regular', updatedAt: '11 jun, 17:21' },
  { id: 's-08', name: 'Henrique Oliveira Lima', registration: '2024.0348', className: 'Informática 1A', course: 'Técnico em Informática', average: 6.4, attendance: 79, status: 'Atenção', updatedAt: '11 jun, 10:12' },
  { id: 's-09', name: 'Isabela Carvalho', registration: '2024.0112', className: 'Edificações 2B', course: 'Técnico em Edificações', average: 8.5, attendance: 95, status: 'Regular', updatedAt: '10 jun, 16:04' },
  { id: 's-10', name: 'João Victor Mendes', registration: '2023.0183', className: 'Administração 3A', course: 'Técnico em Administração', average: 5.9, attendance: 84, status: 'Atenção', updatedAt: '10 jun, 14:40' },
  { id: 's-11', name: 'Larissa Alves Pinto', registration: '2024.0281', className: 'Edificações 2B', course: 'Técnico em Edificações', average: 9.3, attendance: 97, status: 'Regular', updatedAt: '09 jun, 09:28' },
  { id: 's-12', name: 'Mateus Gomes Rocha', registration: '2024.0367', className: 'Informática 1A', course: 'Técnico em Informática', average: 4.8, attendance: 68, status: 'Crítico', updatedAt: '08 jun, 13:52' },
];

export const academicClasses = [
  { id: 'c-01', name: 'Eletrotécnica 2A', course: 'Técnico em Eletrotécnica', students: 32, average: 7.8, attendance: 92, attentionCount: 4, status: 'Em andamento' },
  { id: 'c-02', name: 'Mecânica 1B', course: 'Técnico em Mecânica', students: 29, average: 7.1, attendance: 87, attentionCount: 7, status: 'Em andamento' },
  { id: 'c-03', name: 'Administração 3A', course: 'Técnico em Administração', students: 35, average: 8.2, attendance: 94, attentionCount: 2, status: 'Em andamento' },
  { id: 'c-04', name: 'Informática 1A', course: 'Técnico em Informática', students: 31, average: 6.9, attendance: 83, attentionCount: 8, status: 'Em andamento' },
  { id: 'c-05', name: 'Edificações 2B', course: 'Técnico em Edificações', students: 27, average: 8.0, attendance: 91, attentionCount: 3, status: 'Em andamento' },
];

export const academicSubjects = [
  { id: 'd-01', name: 'Fundamentos de Eletricidade', teacher: 'Marcos Vinícius Tavares', classes: 'Eletrotécnica 2A', average: 7.4, attendance: 91, attentionCount: 5 },
  { id: 'd-02', name: 'Matemática Aplicada', teacher: 'Juliana F. Rocha', classes: 'Mecânica 1B · Informática 1A', average: 6.8, attendance: 85, attentionCount: 11 },
  { id: 'd-03', name: 'Gestão de Processos', teacher: 'Renata Almeida', classes: 'Administração 3A', average: 8.6, attendance: 95, attentionCount: 2 },
  { id: 'd-04', name: 'Desenho Técnico', teacher: 'Rafael Moreira', classes: 'Edificações 2B', average: 7.9, attendance: 92, attentionCount: 4 },
  { id: 'd-05', name: 'Lógica de Programação', teacher: 'Carlos Eduardo Pires', classes: 'Informática 1A', average: 6.2, attendance: 81, attentionCount: 9 },
];

export const academicAlerts = [
  { id: 'a-01', student: 'Daniel Souza Martins', studentId: 's-04', className: 'Informática 1A', signal: 'Frequência abaixo do limite', priority: 'Alta', date: 'Hoje, 09:12', followed: false },
  { id: 'a-02', student: 'Mateus Gomes Rocha', studentId: 's-12', className: 'Informática 1A', signal: 'Queda de desempenho', priority: 'Alta', date: 'Hoje, 08:46', followed: false },
  { id: 'a-03', student: 'Bruno Henrique Alves', studentId: 's-02', className: 'Mecânica 1B', signal: 'Média abaixo de 6,0', priority: 'Média', date: 'Ontem, 16:38', followed: true },
  { id: 'a-04', student: 'João Victor Mendes', studentId: 's-10', className: 'Administração 3A', signal: 'Duas avaliações pendentes', priority: 'Média', date: 'Ontem, 15:04', followed: false },
  { id: 'a-05', student: 'Henrique Oliveira Lima', studentId: 's-08', className: 'Informática 1A', signal: 'Frequência em atenção', priority: 'Baixa', date: '11 jun, 11:19', followed: true },
];

export function getAcademicStudentProfile(student, customHistoryMap = {}) {
  const subjectNames =
    student.course === 'Técnico em Informática'
      ? ['Lógica de Programação', 'Matemática Aplicada', 'Banco de Dados', 'Redes de Computadores']
      : student.course === 'Técnico em Eletrotécnica'
        ? ['Fundamentos de Eletricidade', 'Matemática Aplicada', 'Instalações Elétricas', 'Segurança do Trabalho']
        : student.course === 'Técnico em Mecânica'
          ? ['Desenho Técnico', 'Matemática Aplicada', 'Processos de Fabricação', 'Metrologia']
          : student.course === 'Técnico em Administração'
            ? ['Gestão de Processos', 'Matemática Aplicada', 'Comunicação Empresarial', 'Logística']
            : ['Desenho Técnico', 'Matemática Aplicada', 'Materiais de Construção', 'Topografia'];

  const subjects = subjectNames.map((name, index) => {
    const average = Math.max(
      0,
      Math.min(10, Number((student.average + (1 - index) * 0.25 - index * 0.12).toFixed(1))),
    );
    const attendance = Math.max(0, Math.min(100, student.attendance + (index % 2 === 0 ? 2 : -3)));
    const status =
      average < 5 || attendance < 75 ? 'Crítico' : average < 7 || attendance < 85 ? 'Atenção' : 'Regular';
    const evolution = index === 2 && student.status !== 'Regular' ? 'down' : index === 0 ? 'up' : 'stable';
    const av1 = Math.max(0, Math.min(10, Number((average - 0.3).toFixed(1))));
    const av2 = Math.max(0, Math.min(10, Number((average + 0.2).toFixed(1))));
    const pratica = Math.max(0, Math.min(10, Number((average + 0.1).toFixed(1))));
    return {
      id: `${student.id}-${index + 1}`,
      name,
      av1,
      av2,
      pratica,
      average,
      attendance,
      absences: Math.max(0, Math.round(((100 - attendance) / 100) * 40)),
      totalClasses: 40,
      evolution,
      status,
    };
  });

  const baseHistory = [
    {
      date: '12 jun 2024',
      author: 'Prof. Mariana Costa',
      title: 'Evolução observada após plano de estudos',
      detail:
        'Estudante apresentou melhora nas atividades práticas e manteve frequência regular. Próximo acompanhamento previsto para o fechamento do bimestre.',
    },
    {
      date: '28 mai 2024',
      author: 'Professor responsável',
      title: `Orientação sobre ${subjectNames[1]}`,
      detail:
        'Recomendadas atividades de reforço e revisão dos fundamentos antes da próxima avaliação.',
    },
  ];

  const extra = customHistoryMap[student.id] || [];

  return {
    student,
    subjects,
    history: [...extra, ...baseHistory],
  };
}

// Dados iniciais para Diário de Classe, Chamada Rápida e Oficinas Práticas (FE-018, FE-021 a FE-027)
export const initialWorkshopModules = [
  {
    id: 'm-01',
    code: 'MOD-ELET-01',
    name: 'Oficina de Instalações e Comandos Elétricos',
    className: 'Eletrotécnica 2A',
    subject: 'Fundamentos de Eletricidade',
    lab: 'Laboratório de Eletrotécnica 02',
    workload: '80h',
    safetyNorm: 'NR-10 · Uso obrigatório de EPI',
  },
  {
    id: 'm-02',
    code: 'MOD-MEC-01',
    name: 'Metrologia Dimensional e Usinagem Básica',
    className: 'Mecânica 1B',
    subject: 'Desenho Técnico & Metrologia',
    lab: 'Oficina Mecânica B1',
    workload: '60h',
    safetyNorm: 'NR-12 · Óculos e calçado de segurança',
  },
  {
    id: 'm-03',
    code: 'MOD-INFO-01',
    name: 'Laboratório de Algoritmos e Bancada de Redes',
    className: 'Informática 1A',
    subject: 'Lógica de Programação',
    lab: 'Lab. Informática 04',
    workload: '60h',
    safetyNorm: 'Ergonomia e organização de bancada',
  },
];

export const initialPracticalActivities = [
  {
    id: 'pa-01',
    moduleId: 'm-01',
    className: 'Eletrotécnica 2A',
    title: 'Montagem de Quadro de Comando com Partida Direta e Reversão',
    criteria: 'Precisão da fiação, teste de continuidade, organização do painel e respeito à NR-10',
    dueDate: 'Hoje · Bancadas 01 a 08',
    maxScore: 10,
    completedStudentIds: ['s-01', 's-05'],
  },
  {
    id: 'pa-02',
    moduleId: 'm-01',
    className: 'Eletrotécnica 2A',
    title: 'Medição de Tensão, Corrente e Fator de Potência em Carga Trifásica',
    criteria: 'Uso correto do multímetro/alicate amperímetro e registro da tabela técnica',
    dueDate: '18 jun · Laboratório 02',
    maxScore: 10,
    completedStudentIds: ['s-01'],
  },
  {
    id: 'pa-03',
    moduleId: 'm-02',
    className: 'Mecânica 1B',
    title: 'Aferição de Eixo Escalonado com Paquímetro Milesimal e Micrômetro',
    criteria: 'Tolerância dimensional ISO (±0,02 mm) e leitura sem erro de paralaxe',
    dueDate: 'Hoje · Oficina B1',
    maxScore: 10,
    completedStudentIds: ['s-06'],
  },
  {
    id: 'pa-04',
    moduleId: 'm-03',
    className: 'Informática 1A',
    title: 'Implementação de Estrutura de Repetição e Validação de Dados',
    criteria: 'Código limpo, tratamento de entradas inválidas e execução dos casos de teste',
    dueDate: 'Ontem · Lab 04',
    maxScore: 10,
    completedStudentIds: ['s-08'],
  },
];

// Chamada Rápida por Aluno (P = Presente, F = Falta, J = Justificada)
export const initialAttendanceMap = {
  's-01': 'P',
  's-02': 'P',
  's-03': 'P',
  's-04': 'F',
  's-05': 'P',
  's-06': 'P',
  's-07': 'P',
  's-08': 'J',
  's-09': 'P',
  's-10': 'P',
  's-11': 'P',
  's-12': 'F',
};

// Pedidos de Ajuda e Mural da Turma (FE-038, FE-039, FE-040)
export const initialHelpRequests = [
  {
    id: 'hr-01',
    studentId: 's-04',
    studentName: 'Daniel Souza Martins',
    className: 'Informática 1A',
    subject: 'Lógica de Programação',
    bench: 'Bancada 04',
    urgency: 'Alta',
    status: 'Pendente',
    createdAt: 'Hoje, 09:20',
    question: 'Estou com dificuldade para entender a condição de parada do laço while no exercício 3 da prática.',
    reply: '',
  },
  {
    id: 'hr-02',
    studentId: 's-02',
    studentName: 'Bruno Henrique Alves',
    className: 'Mecânica 1B',
    subject: 'Metrologia',
    bench: 'Bancada 02',
    urgency: 'Média',
    status: 'Pendente',
    createdAt: 'Hoje, 08:50',
    question: 'Poderia conferir minha leitura do nônio no micrômetro externo de 25-50mm antes de eu fechar o relatório?',
    reply: '',
  },
  {
    id: 'hr-03',
    studentId: 's-01',
    studentName: 'Ana Luísa Ribeiro',
    className: 'Eletrotécnica 2A',
    subject: 'Fundamentos de Eletricidade',
    bench: 'Bancada 01',
    urgency: 'Baixa',
    status: 'Respondido',
    createdAt: 'Ontem, 15:10',
    question: 'Professora, podemos usar relé térmico com faixa de ajuste de 4A a 6A na montagem da partida direta?',
    reply: 'Sim, Ana! Como a corrente nominal do motor da bancada é 4,8A, essa faixa de 4A a 6A é a ideal. Parabéns pela atenção ao dimensionamento!',
  },
];

export const initialWallPosts = [
  {
    id: 'wp-01',
    author: 'Prof. Mariana Costa',
    role: 'Docente SENAI',
    targetClass: 'Todas as turmas',
    title: 'Avaliação Prática de Oficina e Fechamento de Frequência',
    content: 'Lembrem-se de conferir o uso completo dos EPIs antes do início das atividades práticas desta semana. O limite regimental de frequência do SENAI é de 75%.',
    date: 'Hoje, 08:00',
    tag: 'Importante',
  },
  {
    id: 'wp-02',
    author: 'Prof. Marcos Vinícius Tavares',
    role: 'Docente · Eletrotécnica',
    targetClass: 'Eletrotécnica 2A',
    title: 'Roteiro da Prática de Comandos Elétricos Liberado',
    content: 'O diagrama multifilar e o checklist de testes de continuidade já estão disponíveis para revisão antes da aula no Laboratório 02.',
    date: 'Ontem, 17:30',
    tag: 'Oficina',
  },
];

// Autoavaliação de Competências e Conquistas do Aluno (FE-030, FE-036, FE-037)
export const initialSelfAssessmentCompetencies = [
  {
    id: 'comp-01',
    name: 'Segurança em Oficina e Normas Técnicas (NR-10 / NR-12)',
    category: 'Competência Técnica',
    teacherLevel: 5,
    studentLevel: 5,
    description: 'Utiliza EPIs corretamente, mantém a bancada organizada e segue procedimentos de bloqueio e segurança.',
  },
  {
    id: 'comp-02',
    name: 'Execução Prática e Precisão nas Medições',
    category: 'Competência Técnica',
    teacherLevel: 4,
    studentLevel: 4,
    description: 'Interpreta diagramas/desenhos técnicos e realiza montagens e aferições dentro da tolerância exigida.',
  },
  {
    id: 'comp-03',
    name: 'Resolução de Problemas e Diagnóstico de Falhas',
    category: 'Competência Metodológica',
    teacherLevel: 4,
    studentLevel: 3,
    description: 'Identifica causas de falhas em circuitos, códigos ou peças com autonomia e raciocínio lógico.',
  },
  {
    id: 'comp-04',
    name: 'Trabalho em Equipe e Colaboração na Bancada',
    category: 'Competência Socioemocional',
    teacherLevel: 5,
    studentLevel: 5,
    description: 'Comunica-se com clareza, apoia colegas na oficina e cumpre os prazos de entrega coletiva.',
  },
];

export const initialStudentBadges = [
  {
    id: 'b-01',
    title: 'Presença Exemplar SENAI',
    description: 'Manteve frequência acima de 95% durante todo o semestre letivo.',
    progress: 100,
    unlocked: true,
    tone: 'green',
  },
  {
    id: 'b-02',
    title: 'Segurança Nota 10 (NR-10 / NR-12)',
    description: 'Concluiu 100% das práticas de laboratório sem nenhuma ocorrência de segurança.',
    progress: 100,
    unlocked: true,
    tone: 'blue',
  },
  {
    id: 'b-03',
    title: 'Destaque em Oficina Prática',
    description: 'Atingiu média superior a 8,5 nas avaliações práticas de bancada.',
    progress: 100,
    unlocked: true,
    tone: 'amber',
  },
  {
    id: 'b-04',
    title: 'Mentoria Colaborativa',
    description: 'Apoiou colegas em 5 atividades práticas em dupla na oficina.',
    progress: 80,
    unlocked: false,
    tone: 'blue',
  },
];

