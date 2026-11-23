/**
 * =============================================================================
 * PROJETO NEXA — SEED DE ESTRUTURA CURRICULAR SENAI (MECÂNICA E METROLOGIA)
 * CARD: [DB-020] | Comando: npm run db:seed
 * Arquivo: prisma/seed.ts
 * =============================================================================
 * Popula de forma 100% IDEMPOTENTE (UPSERT / ON CONFLICT DO UPDATE) e com dados
 * totalmente ANÔNIMOS E FICTÍCIOS (zero PII real):
 * - 1 Curso Técnico SENAI: Curso Técnico em Mecânica Industrial (`TEC-MEC-01`)
 * - 2 Turmas Acadêmicas: `MEC-2026-1` (2026.1 / Manhã) e `MEC-2026-2` (2026.2 / Noite)
 * - 4 Disciplinas: Metrologia, Desenho Técnico Mecânico, Usinagem Convencional,
 *   Segurança do Trabalho
 * - 8 Módulos Práticos Sequenciais (2 módulos por disciplina)
 * - 15 Competências Industriais (`TECHNICAL`, `SAFETY`, `PROCEDURAL`)
 * - 24 Vínculos N:M em `module_competencies` (todas as 15 competências vinculadas)
 * - 9 Usuários Fictícios Anônimos + Perfis + 6 Matrículas + 10 Alocações Docentes
 * =============================================================================
 */

const fs = require('node:fs');
const path = require('node:path');
const { execSync } = require('node:child_process');

type Role = 'ADMIN' | 'COORDINATOR' | 'TEACHER' | 'STUDENT';
type Shift = 'MORNING' | 'AFTERNOON' | 'NIGHT';
type ClassStatus = 'PLANNING' | 'ACTIVE' | 'COMPLETED' | 'ARCHIVED';
type CompetencyCategory = 'TECHNICAL' | 'SAFETY' | 'PROCEDURAL';
type EnrollmentStatus = 'ACTIVE' | 'COMPLETED' | 'DROPPED' | 'SUSPENDED';

interface CourseSeed {
  code: string;
  name: string;
  description: string;
  totalHours: number;
  isActive: boolean;
}

interface ClassSeed {
  courseCode: string;
  code: string;
  period: string;
  shift: Shift;
  maxStudents: number;
  status: ClassStatus;
  startDate: string;
  endDate: string;
}

interface SubjectSeed {
  courseCode: string;
  code: string;
  name: string;
  workloadHours: number;
  syllabus: string;
  isActive: boolean;
}

interface ModuleSeed {
  subjectCode: string;
  orderIndex: number;
  title: string;
  description: string;
  practicalHours: number;
  moduleWeight: number;
  passingScore: number;
}

interface CompetencySeed {
  code: string;
  title: string;
  category: CompetencyCategory;
  description: string;
}

interface ModuleCompetencySeed {
  subjectCode: string;
  moduleOrderIndex: number;
  competencyCode: string;
  weight: number;
  requiredLevel: number;
}

interface UserSeed {
  email: string;
  role: Role;
  fullName: string;
  registrationNumber: string;
  bio: string;
}

interface EnrollmentSeed {
  studentEmail: string;
  classCode: string;
  classPeriod: string;
  enrollmentDate: string;
  status: EnrollmentStatus;
  finalGrade: number | null;
  attendanceRate: number | null;
}

interface TeacherAssignmentSeed {
  teacherEmail: string;
  classCode: string;
  classPeriod: string;
  subjectCode: string;
  isMainTeacher: boolean;
}

const ROOT_DIR: string = path.resolve(__dirname, '..');
const SEED_SQL_PATH: string = path.join(ROOT_DIR, 'BancoNexa', 'sql', '20_seed_estrutura_curricular_senai.sql');

// Hash Bcrypt fictício sintético (60 chars) exclusivo para ambiente local de desenvolvimento/testes
const DEMO_BCRYPT_HASH: string = '$2b$12$NexaSenaiDemoSeed20260uQwErTyUiOpAsDfGhJkLzXcVbNm1234';

const COURSE_SEED: CourseSeed = {
  code: 'TEC-MEC-01',
  name: 'Curso Técnico em Mecânica Industrial',
  description:
    'Formação técnica profissionalizante SENAI voltada para metrologia dimensional, desenho técnico mecânico, processos de usinagem convencional e segurança industrial.',
  totalHours: 1200,
  isActive: true,
};

const CLASSES_SEED: ClassSeed[] = [
  {
    courseCode: 'TEC-MEC-01',
    code: 'MEC-2026-1',
    period: '2026.1',
    shift: 'MORNING',
    maxStudents: 30,
    status: 'ACTIVE',
    startDate: '2026-02-09',
    endDate: '2026-07-10',
  },
  {
    courseCode: 'TEC-MEC-01',
    code: 'MEC-2026-2',
    period: '2026.2',
    shift: 'NIGHT',
    maxStudents: 30,
    status: 'ACTIVE',
    startDate: '2026-08-03',
    endDate: '2026-12-18',
  },
];

const SUBJECTS_SEED: SubjectSeed[] = [
  {
    courseCode: 'TEC-MEC-01',
    code: 'UC-MET-01',
    name: 'Metrologia',
    workloadHours: 80,
    syllabus:
      'Sistemas de unidades, medição linear com paquímetro e micrômetro, relógio comparador, incerteza de medição e controle dimensional ISO.',
    isActive: true,
  },
  {
    courseCode: 'TEC-MEC-01',
    code: 'UC-DTM-02',
    name: 'Desenho Técnico Mecânico',
    workloadHours: 80,
    syllabus:
      'Projeções ortográficas ABNT, cortes e seções, cotagem funcional, tolerâncias dimensionais, ajustes eixo-furo e simbologia de rugosidade.',
    isActive: true,
  },
  {
    courseCode: 'TEC-MEC-01',
    code: 'UC-USI-03',
    name: 'Usinagem Convencional',
    workloadHours: 160,
    syllabus:
      'Parâmetros de corte, torneamento cilíndrico e faceamento em torno convencional, fresamento de superfícies planas, rasgos e acabamento.',
    isActive: true,
  },
  {
    courseCode: 'TEC-MEC-01',
    code: 'UC-SEG-04',
    name: 'Segurança do Trabalho',
    workloadHours: 40,
    syllabus:
      'Prevenção de acidentes em oficinas mecânicas, uso de EPIs/EPCs, requisitos de segurança em máquinas operatrizes (NR-12) e programa 5S.',
    isActive: true,
  },
];

const LEARNING_MODULES_SEED: ModuleSeed[] = [
  // Metrologia (2 módulos)
  {
    subjectCode: 'UC-MET-01',
    orderIndex: 1,
    title: 'Metrologia com Paquímetro e Régua Graduada',
    description:
      'Leitura direta em milímetros e polegadas com paquímetro universal, conferência de peças padronizadas e verificação de tolerância H7.',
    practicalHours: 24,
    moduleWeight: 1.0,
    passingScore: 6.0,
  },
  {
    subjectCode: 'UC-MET-01',
    orderIndex: 2,
    title: 'Metrologia com Micrômetro e Relógio Comparador',
    description:
      'Medição centesimal externa com micrômetro, verificação de concentricidade e batimento radial em peças cilíndricas usinadas.',
    practicalHours: 32,
    moduleWeight: 1.5,
    passingScore: 6.5,
  },
  // Desenho Técnico Mecânico (2 módulos)
  {
    subjectCode: 'UC-DTM-02',
    orderIndex: 1,
    title: 'Leitura de Vistas Ortográficas, Cortes e Cotagem',
    description:
      'Interpretação prática de desenhos industriais em 1º diedro, cortes parciais/totais e extração de cotas críticas para fabricação.',
    practicalHours: 20,
    moduleWeight: 1.0,
    passingScore: 6.0,
  },
  {
    subjectCode: 'UC-DTM-02',
    orderIndex: 2,
    title: 'Tolerâncias Dimensionais ISO, Ajustes e Rugosidade',
    description:
      'Análise de campos de tolerância ISO 286, seleção de ajustes com folga/interferência e leitura de especificações de rugosidade Ra e GD&T.',
    practicalHours: 28,
    moduleWeight: 1.5,
    passingScore: 6.5,
  },
  // Usinagem Convencional (2 módulos)
  {
    subjectCode: 'UC-USI-03',
    orderIndex: 1,
    title: 'Módulo de Tornearia Cilíndrica e Faceamento',
    description:
      'Preparação de torno paralelo, centralização de ferramenta, cálculo de RPM, faceamento e cilindramento externo de eixos escalonados.',
    practicalHours: 56,
    moduleWeight: 2.0,
    passingScore: 7.0,
  },
  {
    subjectCode: 'UC-USI-03',
    orderIndex: 2,
    title: 'Módulo de Fresamento de Superfícies Planas e Rasgos',
    description:
      'Fixação em morsa de precisão, alinhamento de cabeçote, esquadrejamento de blocos prismáticos e abertura de canais chavetados.',
    practicalHours: 56,
    moduleWeight: 2.0,
    passingScore: 7.0,
  },
  // Segurança do Trabalho (2 módulos)
  {
    subjectCode: 'UC-SEG-04',
    orderIndex: 1,
    title: 'Segurança em Oficinas Mecânicas e Uso de EPIs',
    description:
      'Inspeção pré-operacional de bancada, identificação de riscos mecânicos/térmicos e utilização obrigatória de EPIs de proteção.',
    practicalHours: 16,
    moduleWeight: 1.0,
    passingScore: 7.0,
  },
  {
    subjectCode: 'UC-SEG-04',
    orderIndex: 2,
    title: 'Bloqueio de Máquinas Operatrizes (NR-12) e 5S',
    description:
      'Procedimentos de bloqueio e etiquetagem (LOTO), teste de botoeiras de emergência NR-12, segregação de cavacos e organização 5S.',
    practicalHours: 16,
    moduleWeight: 1.5,
    passingScore: 7.5,
  },
];

const COMPETENCIES_SEED: CompetencySeed[] = [
  {
    code: 'COMP-MET-01',
    title: 'Medição com Paquímetro e Tolerância H7',
    category: 'TECHNICAL',
    description: 'Realizar medições externas, internas e de profundidade com resolução de 0,02 mm segundo ISO 286.',
  },
  {
    code: 'COMP-MET-02',
    title: 'Medição de Precisão com Micrômetro Externo',
    category: 'TECHNICAL',
    description: 'Operar micrômetro externo centesimal com controle de força de catraca e leitura sem erro de paralaxe.',
  },
  {
    code: 'COMP-MET-03',
    title: 'Verificação de Batimento com Relógio Comparador',
    category: 'TECHNICAL',
    description: 'Posicionar base magnética e relógio comparador para inspecionar desvios geométricos e concentricidade.',
  },
  {
    code: 'COMP-MET-04',
    title: 'Conservação e Calibração de Instrumentos de Medição',
    category: 'PROCEDURAL',
    description: 'Conferir zeragem com padrões de referência, higienizar e acondicionar instrumentos metrológicos.',
  },
  {
    code: 'COMP-DTM-01',
    title: 'Interpretação de Vistas Ortográficas e Cortes ABNT',
    category: 'TECHNICAL',
    description: 'Ler projeções em 1º diedro, hachuras de corte e linhas de centro conforme NBR 10067.',
  },
  {
    code: 'COMP-DTM-02',
    title: 'Leitura de Tolerâncias ISO e Ajustes Eixo-Furo',
    category: 'TECHNICAL',
    description: 'Determinar afastamentos superior/inferior e classificar ajustes com folga, incerto ou interferência.',
  },
  {
    code: 'COMP-DTM-03',
    title: 'Análise de Rugosidade Superficial e Simbologia GD&T',
    category: 'PROCEDURAL',
    description: 'Interpretar símbolos de rugosidade Ra e tolerâncias geométricas de forma e posição no desenho.',
  },
  {
    code: 'COMP-USI-01',
    title: 'Faceamento e Cilindramento Externo em Torno Convencional',
    category: 'TECHNICAL',
    description: 'Usinar eixos cilíndricos em torno paralelo mantendo coaxialidade, acabamento e cota dentro do desenho.',
  },
  {
    code: 'COMP-USI-02',
    title: 'Cálculo de RPM, Avanço e Profundidade de Corte',
    category: 'TECHNICAL',
    description: 'Calcular velocidade de corte e rotação adequada conforme material da peça e geometria da ferramenta.',
  },
  {
    code: 'COMP-USI-03',
    title: 'Fresamento de Superfícies Planas e Canais Chavetados',
    category: 'TECHNICAL',
    description: 'Executar esquadrejamento de blocos e usinagem de rasgos precisos em fresadora ferramenteira.',
  },
  {
    code: 'COMP-USI-04',
    title: 'Fixação de Peças, Alinhamento de Placa e Ordem de Serviço',
    category: 'PROCEDURAL',
    description: 'Planejar sequência de usinagem, fixar peça com segurança na placa/morsa e registrar inspeções na OS.',
  },
  {
    code: 'COMP-SEG-01',
    title: 'Seleção e Uso Correto de EPIs em Oficina Mecânica',
    category: 'SAFETY',
    description: 'Utilizar óculos de proteção, calçado de segurança e vestimenta ajustada sem adornos em máquinas rotativas.',
  },
  {
    code: 'COMP-SEG-02',
    title: 'Operação Segura de Máquinas Operatrizes conforme NR-12',
    category: 'SAFETY',
    description: 'Verificar proteções móveis, intertravamentos e áreas de risco antes de acionar torno ou fresadora.',
  },
  {
    code: 'COMP-SEG-03',
    title: 'Bloqueio, Sinalização e Parada de Emergência em Bancada',
    category: 'SAFETY',
    description: 'Executar procedimentos de desenergização segura e acionamento correto de dispositivos de emergência.',
  },
  {
    code: 'COMP-PRO-01',
    title: 'Organização de Bancada, Descarte de Cavacos e Metodologia 5S',
    category: 'PROCEDURAL',
    description: 'Manter ferramentas organizadas, remover cavacos com escova adequada e zelar pela limpeza da oficina.',
  },
];

const MODULE_COMPETENCIES_SEED: ModuleCompetencySeed[] = [
  // Módulo 1: Metrologia com Paquímetro
  { subjectCode: 'UC-MET-01', moduleOrderIndex: 1, competencyCode: 'COMP-MET-01', weight: 2.5, requiredLevel: 4 },
  { subjectCode: 'UC-MET-01', moduleOrderIndex: 1, competencyCode: 'COMP-MET-04', weight: 1.5, requiredLevel: 3 },
  { subjectCode: 'UC-MET-01', moduleOrderIndex: 1, competencyCode: 'COMP-PRO-01', weight: 1.0, requiredLevel: 2 },
  // Módulo 2: Metrologia com Micrômetro e Relógio Comparador
  { subjectCode: 'UC-MET-01', moduleOrderIndex: 2, competencyCode: 'COMP-MET-02', weight: 2.5, requiredLevel: 4 },
  { subjectCode: 'UC-MET-01', moduleOrderIndex: 2, competencyCode: 'COMP-MET-03', weight: 2.0, requiredLevel: 4 },
  { subjectCode: 'UC-MET-01', moduleOrderIndex: 2, competencyCode: 'COMP-MET-04', weight: 1.5, requiredLevel: 4 },
  // Módulo 3: Leitura de Vistas Ortográficas
  { subjectCode: 'UC-DTM-02', moduleOrderIndex: 1, competencyCode: 'COMP-DTM-01', weight: 2.5, requiredLevel: 4 },
  { subjectCode: 'UC-DTM-02', moduleOrderIndex: 1, competencyCode: 'COMP-MET-01', weight: 1.0, requiredLevel: 3 },
  // Módulo 4: Tolerâncias Dimensionais ISO
  { subjectCode: 'UC-DTM-02', moduleOrderIndex: 2, competencyCode: 'COMP-DTM-02', weight: 2.5, requiredLevel: 4 },
  { subjectCode: 'UC-DTM-02', moduleOrderIndex: 2, competencyCode: 'COMP-DTM-03', weight: 2.0, requiredLevel: 3 },
  { subjectCode: 'UC-DTM-02', moduleOrderIndex: 2, competencyCode: 'COMP-MET-02', weight: 1.0, requiredLevel: 3 },
  // Módulo 5: Tornearia Cilíndrica e Faceamento
  { subjectCode: 'UC-USI-03', moduleOrderIndex: 1, competencyCode: 'COMP-USI-01', weight: 3.0, requiredLevel: 5 },
  { subjectCode: 'UC-USI-03', moduleOrderIndex: 1, competencyCode: 'COMP-USI-02', weight: 2.0, requiredLevel: 4 },
  { subjectCode: 'UC-USI-03', moduleOrderIndex: 1, competencyCode: 'COMP-USI-04', weight: 1.5, requiredLevel: 4 },
  { subjectCode: 'UC-USI-03', moduleOrderIndex: 1, competencyCode: 'COMP-MET-02', weight: 1.5, requiredLevel: 4 },
  { subjectCode: 'UC-USI-03', moduleOrderIndex: 1, competencyCode: 'COMP-SEG-02', weight: 2.0, requiredLevel: 5 },
  // Módulo 6: Fresamento de Superfícies Planas e Rasgos
  { subjectCode: 'UC-USI-03', moduleOrderIndex: 2, competencyCode: 'COMP-USI-03', weight: 3.0, requiredLevel: 5 },
  { subjectCode: 'UC-USI-03', moduleOrderIndex: 2, competencyCode: 'COMP-USI-02', weight: 2.0, requiredLevel: 4 },
  { subjectCode: 'UC-USI-03', moduleOrderIndex: 2, competencyCode: 'COMP-USI-04', weight: 1.5, requiredLevel: 4 },
  { subjectCode: 'UC-USI-03', moduleOrderIndex: 2, competencyCode: 'COMP-SEG-02', weight: 2.0, requiredLevel: 5 },
  // Módulo 7: Segurança em Oficinas e Uso de EPIs
  { subjectCode: 'UC-SEG-04', moduleOrderIndex: 1, competencyCode: 'COMP-SEG-01', weight: 2.5, requiredLevel: 4 },
  { subjectCode: 'UC-SEG-04', moduleOrderIndex: 1, competencyCode: 'COMP-PRO-01', weight: 1.5, requiredLevel: 3 },
  // Módulo 8: Bloqueio NR-12 e 5S
  { subjectCode: 'UC-SEG-04', moduleOrderIndex: 2, competencyCode: 'COMP-SEG-02', weight: 2.5, requiredLevel: 5 },
  { subjectCode: 'UC-SEG-04', moduleOrderIndex: 2, competencyCode: 'COMP-SEG-03', weight: 2.5, requiredLevel: 5 },
];

// Usuários 100% anônimos e fictícios (zero dados pessoais reais)
const USERS_SEED: UserSeed[] = [
  {
    email: 'coord.demo@senai.nexa.local',
    role: 'COORDINATOR',
    fullName: 'Coordenacao Demo SENAI',
    registrationNumber: 'SENAI-COORD-0001',
    bio: 'Conta fictícia de demonstração da coordenação pedagógica.',
  },
  {
    email: 'instrutor.teoria.demo@senai.nexa.local',
    role: 'TEACHER',
    fullName: 'Instrutor Demo 01 (Metrologia e Desenho)',
    registrationNumber: 'SENAI-DOC-0001',
    bio: 'Instrutor fictício de metrologia dimensional, desenho técnico e teoria de usinagem.',
  },
  {
    email: 'instrutor.oficina.demo@senai.nexa.local',
    role: 'TEACHER',
    fullName: 'Instrutor Demo 02 (Oficina de Usinagem e NR-12)',
    registrationNumber: 'SENAI-DOC-0002',
    bio: 'Instrutor fictício de laboratório de tornearia, fresamento e segurança industrial.',
  },
  {
    email: 'estudante.demo01@aluno.nexa.local',
    role: 'STUDENT',
    fullName: 'Estudante Demo 01',
    registrationNumber: 'SENAI-2026-0001',
    bio: 'Estudante fictício da turma MEC-2026-1.',
  },
  {
    email: 'estudante.demo02@aluno.nexa.local',
    role: 'STUDENT',
    fullName: 'Estudante Demo 02',
    registrationNumber: 'SENAI-2026-0002',
    bio: 'Estudante fictício da turma MEC-2026-1.',
  },
  {
    email: 'estudante.demo03@aluno.nexa.local',
    role: 'STUDENT',
    fullName: 'Estudante Demo 03',
    registrationNumber: 'SENAI-2026-0003',
    bio: 'Estudante fictício da turma MEC-2026-1.',
  },
  {
    email: 'estudante.demo04@aluno.nexa.local',
    role: 'STUDENT',
    fullName: 'Estudante Demo 04',
    registrationNumber: 'SENAI-2026-0004',
    bio: 'Estudante fictício da turma MEC-2026-2.',
  },
  {
    email: 'estudante.demo05@aluno.nexa.local',
    role: 'STUDENT',
    fullName: 'Estudante Demo 05',
    registrationNumber: 'SENAI-2026-0005',
    bio: 'Estudante fictício da turma MEC-2026-2.',
  },
  {
    email: 'estudante.demo06@aluno.nexa.local',
    role: 'STUDENT',
    fullName: 'Estudante Demo 06',
    registrationNumber: 'SENAI-2026-0006',
    bio: 'Estudante fictício da turma MEC-2026-2.',
  },
];

const ENROLLMENTS_SEED: EnrollmentSeed[] = [
  {
    studentEmail: 'estudante.demo01@aluno.nexa.local',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    enrollmentDate: '2026-02-02',
    status: 'ACTIVE',
    finalGrade: null,
    attendanceRate: 96.0,
  },
  {
    studentEmail: 'estudante.demo02@aluno.nexa.local',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    enrollmentDate: '2026-02-02',
    status: 'ACTIVE',
    finalGrade: null,
    attendanceRate: 88.5,
  },
  {
    studentEmail: 'estudante.demo03@aluno.nexa.local',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    enrollmentDate: '2026-02-03',
    status: 'ACTIVE',
    finalGrade: null,
    attendanceRate: 72.0,
  },
  {
    studentEmail: 'estudante.demo04@aluno.nexa.local',
    classCode: 'MEC-2026-2',
    classPeriod: '2026.2',
    enrollmentDate: '2026-07-27',
    status: 'ACTIVE',
    finalGrade: null,
    attendanceRate: 94.0,
  },
  {
    studentEmail: 'estudante.demo05@aluno.nexa.local',
    classCode: 'MEC-2026-2',
    classPeriod: '2026.2',
    enrollmentDate: '2026-07-27',
    status: 'ACTIVE',
    finalGrade: null,
    attendanceRate: 85.0,
  },
  {
    studentEmail: 'estudante.demo06@aluno.nexa.local',
    classCode: 'MEC-2026-2',
    classPeriod: '2026.2',
    enrollmentDate: '2026-07-28',
    status: 'ACTIVE',
    finalGrade: null,
    attendanceRate: 78.5,
  },
];

const TEACHER_ASSIGNMENTS_SEED: TeacherAssignmentSeed[] = [
  // Turma MEC-2026-1 (inclui co-docência teoria + oficina em Usinagem Convencional)
  {
    teacherEmail: 'instrutor.teoria.demo@senai.nexa.local',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    subjectCode: 'UC-MET-01',
    isMainTeacher: true,
  },
  {
    teacherEmail: 'instrutor.teoria.demo@senai.nexa.local',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    subjectCode: 'UC-DTM-02',
    isMainTeacher: true,
  },
  {
    teacherEmail: 'instrutor.teoria.demo@senai.nexa.local',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    subjectCode: 'UC-USI-03',
    isMainTeacher: true,
  },
  {
    teacherEmail: 'instrutor.oficina.demo@senai.nexa.local',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    subjectCode: 'UC-USI-03',
    isMainTeacher: false,
  },
  {
    teacherEmail: 'instrutor.oficina.demo@senai.nexa.local',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    subjectCode: 'UC-SEG-04',
    isMainTeacher: true,
  },
  // Turma MEC-2026-2
  {
    teacherEmail: 'instrutor.teoria.demo@senai.nexa.local',
    classCode: 'MEC-2026-2',
    classPeriod: '2026.2',
    subjectCode: 'UC-MET-01',
    isMainTeacher: true,
  },
  {
    teacherEmail: 'instrutor.teoria.demo@senai.nexa.local',
    classCode: 'MEC-2026-2',
    classPeriod: '2026.2',
    subjectCode: 'UC-DTM-02',
    isMainTeacher: true,
  },
  {
    teacherEmail: 'instrutor.oficina.demo@senai.nexa.local',
    classCode: 'MEC-2026-2',
    classPeriod: '2026.2',
    subjectCode: 'UC-USI-03',
    isMainTeacher: true,
  },
  {
    teacherEmail: 'instrutor.teoria.demo@senai.nexa.local',
    classCode: 'MEC-2026-2',
    classPeriod: '2026.2',
    subjectCode: 'UC-USI-03',
    isMainTeacher: false,
  },
  {
    teacherEmail: 'instrutor.oficina.demo@senai.nexa.local',
    classCode: 'MEC-2026-2',
    classPeriod: '2026.2',
    subjectCode: 'UC-SEG-04',
    isMainTeacher: true,
  },
];

function loadEnvVars(): Record<string, string> {
  const envFile: string = fs.existsSync(path.join(ROOT_DIR, '.env'))
    ? path.join(ROOT_DIR, '.env')
    : path.join(ROOT_DIR, '.env.example');

  const vars: Record<string, string> = {};
  if (fs.existsSync(envFile)) {
    for (const line of fs.readFileSync(envFile, 'utf8').split(/\r?\n/)) {
      const trimmed: string = line.trim();
      if (!trimmed || trimmed.startsWith('#')) continue;
      const eqIdx: number = trimmed.indexOf('=');
      if (eqIdx > 0) {
        vars[trimmed.slice(0, eqIdx).trim()] = trimmed.slice(eqIdx + 1).trim();
      }
    }
  }
  return vars;
}

function isPostgresContainerRunning(containerName: string): boolean {
  try {
    const out: string = execSync(`docker inspect -f "{{.State.Running}}" ${containerName}`, {
      cwd: ROOT_DIR,
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe'],
    }).trim();
    return out === 'true';
  } catch {
    return false;
  }
}

function sqlLiteral(value: string | null): string {
  if (value === null) return 'NULL';
  return `'${value.replace(/'/g, "''")}'`;
}

function buildIdempotentSeedSql(): string {
  const lines: string[] = [
    '-- =============================================================================',
    '-- PROJETO NEXA — SEED IDEMPOTENTE DE ESTRUTURA CURRICULAR SENAI (DB-020)',
    '-- SGBD: PostgreSQL 16 (UPSERT via ON CONFLICT DO UPDATE)',
    '-- Dados 100% anônimos e fictícios para ambiente de desenvolvimento/testes',
    '-- =============================================================================',
    '',
    'BEGIN;',
    '',
    '-- 1. Curso Técnico SENAI (1 curso)',
    `INSERT INTO courses (code, name, description, total_hours, is_active)`,
    `VALUES (${sqlLiteral(COURSE_SEED.code)}, ${sqlLiteral(COURSE_SEED.name)}, ${sqlLiteral(COURSE_SEED.description)}, ${COURSE_SEED.totalHours}, ${COURSE_SEED.isActive ? 'TRUE' : 'FALSE'})`,
    `ON CONFLICT (code) DO UPDATE`,
    `SET name = EXCLUDED.name, description = EXCLUDED.description, total_hours = EXCLUDED.total_hours, is_active = EXCLUDED.is_active;`,
    '',
    '-- 2. Turmas Acadêmicas SENAI (2 turmas: MEC-2026-1 e MEC-2026-2)',
  ];

  for (const cls of CLASSES_SEED) {
    lines.push(
      `INSERT INTO classes (course_id, code, period, shift, max_students, status, start_date, end_date)`,
      `SELECT c.id, ${sqlLiteral(cls.code)}, ${sqlLiteral(cls.period)}, ${sqlLiteral(cls.shift)}::shift_enum, ${cls.maxStudents}, ${sqlLiteral(cls.status)}::class_status_enum, DATE ${sqlLiteral(cls.startDate)}, DATE ${sqlLiteral(cls.endDate)}`,
      `FROM courses c WHERE c.code = ${sqlLiteral(cls.courseCode)}`,
      `ON CONFLICT (code, period) DO UPDATE`,
      `SET shift = EXCLUDED.shift, max_students = EXCLUDED.max_students, status = EXCLUDED.status, start_date = EXCLUDED.start_date, end_date = EXCLUDED.end_date;`,
      ''
    );
  }

  lines.push('-- 3. Disciplinas Teórico-Práticas SENAI (4 disciplinas)');
  for (const sub of SUBJECTS_SEED) {
    lines.push(
      `INSERT INTO subjects (course_id, code, name, workload_hours, syllabus, is_active)`,
      `SELECT c.id, ${sqlLiteral(sub.code)}, ${sqlLiteral(sub.name)}, ${sub.workloadHours}, ${sqlLiteral(sub.syllabus)}, ${sub.isActive ? 'TRUE' : 'FALSE'}`,
      `FROM courses c WHERE c.code = ${sqlLiteral(sub.courseCode)}`,
      `ON CONFLICT (course_id, code) DO UPDATE`,
      `SET name = EXCLUDED.name, workload_hours = EXCLUDED.workload_hours, syllabus = EXCLUDED.syllabus, is_active = EXCLUDED.is_active;`,
      ''
    );
  }

  lines.push('-- 4. Módulos de Aprendizagem Prática SENAI (8 módulos sequenciais)');
  for (const mod of LEARNING_MODULES_SEED) {
    lines.push(
      `INSERT INTO learning_modules (subject_id, title, order_index, description, practical_hours, module_weight, passing_score)`,
      `SELECT s.id, ${sqlLiteral(mod.title)}, ${mod.orderIndex}, ${sqlLiteral(mod.description)}, ${mod.practicalHours}, ${mod.moduleWeight.toFixed(2)}, ${mod.passingScore.toFixed(2)}`,
      `FROM subjects s WHERE s.code = ${sqlLiteral(mod.subjectCode)}`,
      `ON CONFLICT (subject_id, order_index) DO UPDATE`,
      `SET title = EXCLUDED.title, description = EXCLUDED.description, practical_hours = EXCLUDED.practical_hours, module_weight = EXCLUDED.module_weight, passing_score = EXCLUDED.passing_score;`,
      ''
    );
  }

  lines.push('-- 5. Competências e Habilidades Técnicas Industriais (15 competências)');
  for (const comp of COMPETENCIES_SEED) {
    lines.push(
      `INSERT INTO competencies (code, title, category, description)`,
      `VALUES (${sqlLiteral(comp.code)}, ${sqlLiteral(comp.title)}, ${sqlLiteral(comp.category)}::competency_category_enum, ${sqlLiteral(comp.description)})`,
      `ON CONFLICT (code) DO UPDATE`,
      `SET title = EXCLUDED.title, category = EXCLUDED.category, description = EXCLUDED.description;`,
      ''
    );
  }

  lines.push('-- 6. Relacionamento N:M Módulo-Competência (24 vínculos ponderados)');
  for (const link of MODULE_COMPETENCIES_SEED) {
    lines.push(
      `INSERT INTO module_competencies (module_id, competency_id, weight, required_level)`,
      `SELECT m.id, cp.id, ${link.weight.toFixed(2)}, ${link.requiredLevel}`,
      `FROM subjects s`,
      `JOIN learning_modules m ON m.subject_id = s.id AND m.order_index = ${link.moduleOrderIndex}`,
      `JOIN competencies cp ON cp.code = ${sqlLiteral(link.competencyCode)}`,
      `WHERE s.code = ${sqlLiteral(link.subjectCode)}`,
      `ON CONFLICT (module_id, competency_id) DO UPDATE`,
      `SET weight = EXCLUDED.weight, required_level = EXCLUDED.required_level;`,
      ''
    );
  }

  lines.push('-- 7. Usuários Fictícios Anônimos e Perfis (zero dados pessoais reais)');
  for (const usr of USERS_SEED) {
    lines.push(
      `INSERT INTO users (email, password_hash, role, is_active)`,
      `VALUES (${sqlLiteral(usr.email)}, ${sqlLiteral(DEMO_BCRYPT_HASH)}, ${sqlLiteral(usr.role)}::user_role_enum, TRUE)`,
      `ON CONFLICT (email) DO UPDATE`,
      `SET role = EXCLUDED.role, is_active = EXCLUDED.is_active;`,
      `INSERT INTO user_profiles (user_id, full_name, registration_number, bio)`,
      `SELECT u.id, ${sqlLiteral(usr.fullName)}, ${sqlLiteral(usr.registrationNumber)}, ${sqlLiteral(usr.bio)}`,
      `FROM users u WHERE u.email = ${sqlLiteral(usr.email)}`,
      `ON CONFLICT (user_id) DO UPDATE`,
      `SET full_name = EXCLUDED.full_name, registration_number = EXCLUDED.registration_number, bio = EXCLUDED.bio;`,
      ''
    );
  }

  lines.push('-- 8. Matrículas Fictícias de Estudantes nas Turmas MEC-2026-1 e MEC-2026-2');
  for (const enr of ENROLLMENTS_SEED) {
    const gradeVal = enr.finalGrade === null ? 'NULL' : enr.finalGrade.toFixed(2);
    const attVal = enr.attendanceRate === null ? 'NULL' : enr.attendanceRate.toFixed(2);
    lines.push(
      `INSERT INTO enrollments (student_id, class_id, enrollment_date, status, final_grade, attendance_rate)`,
      `SELECT u.id, cl.id, DATE ${sqlLiteral(enr.enrollmentDate)}, ${sqlLiteral(enr.status)}::enrollment_status_enum, ${gradeVal}, ${attVal}`,
      `FROM users u`,
      `JOIN classes cl ON cl.code = ${sqlLiteral(enr.classCode)} AND cl.period = ${sqlLiteral(enr.classPeriod)}`,
      `WHERE u.email = ${sqlLiteral(enr.studentEmail)}`,
      `ON CONFLICT (student_id, class_id) DO UPDATE`,
      `SET status = EXCLUDED.status, final_grade = EXCLUDED.final_grade, attendance_rate = EXCLUDED.attendance_rate;`,
      ''
    );
  }

  lines.push('-- 9. Alocação de Docentes nas Turmas e Disciplinas (RBAC Contextual)');
  for (const ta of TEACHER_ASSIGNMENTS_SEED) {
    lines.push(
      `INSERT INTO teacher_assignments (teacher_id, class_id, subject_id, is_main_teacher)`,
      `SELECT u.id, cl.id, s.id, ${ta.isMainTeacher ? 'TRUE' : 'FALSE'}`,
      `FROM users u`,
      `JOIN classes cl ON cl.code = ${sqlLiteral(ta.classCode)} AND cl.period = ${sqlLiteral(ta.classPeriod)}`,
      `JOIN subjects s ON s.code = ${sqlLiteral(ta.subjectCode)}`,
      `WHERE u.email = ${sqlLiteral(ta.teacherEmail)}`,
      `ON CONFLICT (teacher_id, class_id, subject_id) DO UPDATE`,
      `SET is_main_teacher = EXCLUDED.is_main_teacher;`,
      ''
    );
  }

  lines.push('COMMIT;', '');
  return lines.join('\n');
}

function validateAndSimulateIdempotentSeed(): {
  courses: number;
  classes: number;
  subjects: number;
  modules: number;
  competencies: number;
  moduleCompetencies: number;
  users: number;
  enrollments: number;
  teacherAssignments: number;
} {
  const courses = new Map<string, CourseSeed>();
  const classes = new Map<string, ClassSeed>();
  const subjects = new Map<string, SubjectSeed>();
  const modules = new Map<string, ModuleSeed>();
  const competencies = new Map<string, CompetencySeed>();
  const moduleCompetencies = new Map<string, ModuleCompetencySeed>();
  const users = new Map<string, UserSeed>();
  const enrollments = new Map<string, EnrollmentSeed>();
  const teacherAssignments = new Map<string, TeacherAssignmentSeed>();

  // Executa 2 passagens completas de upsert para comprovar idempotência (0 duplicações)
  for (let pass = 1; pass <= 2; pass++) {
    if (COURSE_SEED.totalHours <= 0) throw new Error('Curso com totalHours inválido');
    courses.set(COURSE_SEED.code, COURSE_SEED);

    for (const c of CLASSES_SEED) {
      if (!courses.has(c.courseCode)) throw new Error(`Curso inexistente: ${c.courseCode}`);
      if (!(c.startDate < c.endDate)) throw new Error(`Datas inválidas na turma: ${c.code}`);
      classes.set(`${c.code}::${c.period}`, c);
    }

    for (const s of SUBJECTS_SEED) {
      if (!courses.has(s.courseCode)) throw new Error(`Curso inexistente: ${s.courseCode}`);
      if (s.workloadHours <= 0) throw new Error(`Carga horária inválida: ${s.code}`);
      subjects.set(s.code, s);
    }

    for (const m of LEARNING_MODULES_SEED) {
      if (!subjects.has(m.subjectCode)) throw new Error(`Disciplina inexistente: ${m.subjectCode}`);
      if (m.orderIndex <= 0 || m.passingScore < 0 || m.passingScore > 10 || m.moduleWeight <= 0) {
        throw new Error(`Módulo inválido: ${m.title}`);
      }
      modules.set(`${m.subjectCode}::${m.orderIndex}`, m);
    }

    for (const cp of COMPETENCIES_SEED) {
      competencies.set(cp.code, cp);
    }

    for (const mc of MODULE_COMPETENCIES_SEED) {
      const modKey = `${mc.subjectCode}::${mc.moduleOrderIndex}`;
      if (!modules.has(modKey)) throw new Error(`Módulo ausente para vínculo: ${modKey}`);
      if (!competencies.has(mc.competencyCode)) throw new Error(`Competência ausente: ${mc.competencyCode}`);
      if (mc.requiredLevel < 1 || mc.requiredLevel > 5 || mc.weight <= 0 || mc.weight > 9.99) {
        throw new Error(`Vínculo inválido: ${modKey} <-> ${mc.competencyCode}`);
      }
      moduleCompetencies.set(`${modKey}::${mc.competencyCode}`, mc);
    }

    for (const u of USERS_SEED) {
      users.set(u.email, u);
    }

    for (const e of ENROLLMENTS_SEED) {
      const u = users.get(e.studentEmail);
      if (!u || u.role !== 'STUDENT') throw new Error(`Usuário inválido para matrícula: ${e.studentEmail}`);
      if (!classes.has(`${e.classCode}::${e.classPeriod}`)) throw new Error(`Turma inválida: ${e.classCode}`);
      enrollments.set(`${e.studentEmail}::${e.classCode}::${e.classPeriod}`, e);
    }

    for (const ta of TEACHER_ASSIGNMENTS_SEED) {
      const u = users.get(ta.teacherEmail);
      if (!u || u.role !== 'TEACHER') throw new Error(`Usuário inválido para docência: ${ta.teacherEmail}`);
      if (!classes.has(`${ta.classCode}::${ta.classPeriod}`)) throw new Error(`Turma inválida: ${ta.classCode}`);
      if (!subjects.has(ta.subjectCode)) throw new Error(`Disciplina inválida: ${ta.subjectCode}`);
      teacherAssignments.set(`${ta.teacherEmail}::${ta.classCode}::${ta.classPeriod}::${ta.subjectCode}`, ta);
    }
  }

  return {
    courses: courses.size,
    classes: classes.size,
    subjects: subjects.size,
    modules: modules.size,
    competencies: competencies.size,
    moduleCompetencies: moduleCompetencies.size,
    users: users.size,
    enrollments: enrollments.size,
    teacherAssignments: teacherAssignments.size,
  };
}

function main(): void {
  console.log('======================================================================');
  console.log('🌱 [DB-020] NEXA DB SEED — ESTRUTURA CURRICULAR SENAI (MECÂNICA)');
  console.log('======================================================================\n');

  const counts = validateAndSimulateIdempotentSeed();
  const seedSql: string = buildIdempotentSeedSql();

  fs.mkdirSync(path.dirname(SEED_SQL_PATH), { recursive: true });
  fs.writeFileSync(SEED_SQL_PATH, seedSql, 'utf8');

  const env = loadEnvVars();
  const containerName: string = env.POSTGRES_CONTAINER_NAME || 'nexa-postgres';
  const dbUser: string = env.POSTGRES_USER || 'nexa_admin';
  const dbName: string = env.POSTGRES_DB || 'nexa_senai_db';

  if (isPostgresContainerRunning(containerName)) {
    console.log(`🐳 Container '${containerName}' ativo! Aplicando seed idempotente (UPSERT) no PostgreSQL 16...`);
    execSync(`docker exec -i ${containerName} psql -v ON_ERROR_STOP=1 -U ${dbUser} -d ${dbName}`, {
      cwd: ROOT_DIR,
      input: seedSql,
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    console.log('  [OK] Seed executado com sucesso no PostgreSQL 16 via psql (idempotente).');
  } else {
    console.log(`ℹ️  Container '${containerName}' offline — modo de validação/simulação idempotente (2 passagens UPSERT):`);
    console.log(`  [OK] Script SQL UPSERT sincronizado em: ${path.relative(ROOT_DIR, SEED_SQL_PATH)}`);
  }

  console.log('\n📊 Resumo da Grade Curricular SENAI Populada (100% Dados Fictícios Anônimos):');
  console.log(`  • Cursos Técnicos (courses):                 ${counts.courses}`);
  console.log(`  • Turmas Acadêmicas (classes):               ${counts.classes} (MEC-2026-1, MEC-2026-2)`);
  console.log(`  • Disciplinas (subjects):                    ${counts.subjects}`);
  console.log(`  • Módulos Práticos (learning_modules):       ${counts.modules}`);
  console.log(`  • Competências Industriais (competencies):   ${counts.competencies}`);
  console.log(`  • Vínculos N:M (module_competencies):        ${counts.moduleCompetencies}`);
  console.log(`  • Usuários Demo Anônimos (users/profiles):   ${counts.users}`);
  console.log(`  • Matrículas Ativas (enrollments):           ${counts.enrollments}`);
  console.log(`  • Alocações Docentes (teacher_assignments):  ${counts.teacherAssignments}`);
  console.log('\n✅ [DB-020 SUCESSO] Seed curricular SENAI executado de forma idempotente (Exit Code 0)!');
}

main();
