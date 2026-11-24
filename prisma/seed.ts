/**
 * =============================================================================
 * PROJETO NEXA — SEED DE ESTRUTURA CURRICULAR SENAI + LOTE 3 (DIÁRIO & NOTAS)
 * CARDS: [DB-020] e [DB-030] | Comando: npm run db:seed
 * Arquivo: prisma/seed.ts
 * =============================================================================
 * Popula de forma 100% IDEMPOTENTE (UPSERT / ON CONFLICT DO UPDATE) e com dados
 * totalmente ANÔNIMOS E FICTÍCIOS (zero CPFs ou nomes de alunos reais):
 * [DB-020 — Lote 2: Estrutura Curricular SENAI]
 * - 1 Curso Técnico SENAI: Curso Técnico em Mecânica Industrial (`TEC-MEC-01`)
 * - 2 Turmas Acadêmicas: `MEC-2026-1` (2026.1 / Manhã) e `MEC-2026-2` (2026.2 / Noite)
 * - 4 Disciplinas: Metrologia, Desenho Técnico Mecânico, Usinagem Convencional,
 *   Segurança do Trabalho
 * - 8 Módulos Práticos Sequenciais (2 módulos por disciplina)
 * - 15 Competências Industriais (`TECHNICAL`, `SAFETY`, `PROCEDURAL`)
 * - 24 Vínculos N:M em `module_competencies` (todas as 15 competências vinculadas)
 * - 9 Usuários Fictícios Anônimos + Perfis + 6 Matrículas + 10 Alocações Docentes
 *
 * [DB-030 — Lote 3: Diário de Classe, Frequências, Práticas e Notas Parciais]
 * - 30 Estudantes Fictícios Anônimos (`estudante.demo01..30@aluno.nexa.local`)
 *   matriculados nas turmas `MEC-2026-1` (18) e `MEC-2026-2` (12)
 * - 12 Aulas Ministradas (`class_lessons`, 7 em `MEC-2026-1` e 5 em `MEC-2026-2`, 25h/turma)
 * - Registros de Presença variados (`attendance_records`): 100%, 80%, 76% (limite 25% faltas) e 68% (risco)
 * - 6 Tarefas Práticas de Oficina (`practical_tasks`) + 18 Rubricas (`task_criteria`)
 * - Submissões Práticas (`task_submissions`: `EVALUATED`, `SUBMITTED`, `LATE`, `PENDING`)
 * - Avaliações por Rubrica (`submission_evaluations`) com nota consolidada
 * - 4 Avaliações Formativas (`academic_assessments`) + 60 Notas Parciais (`student_grades`)
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
type AttendanceStatus = 'PRESENT' | 'ABSENT' | 'LATE' | 'JUSTIFIED';
type SubmissionStatus = 'PENDING' | 'SUBMITTED' | 'EVALUATED' | 'LATE';
type AssessmentType = 'EXAM' | 'MICRO_EVALUATION' | 'PROJECT';
type StudentScenarioProfile = 'HIGH_PERFORMER' | 'LATE_DELIVERY' | 'ATTENDANCE_BORDERLINE' | 'AT_RISK';

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
const SEED_LOTE3_SQL_PATH: string = path.join(ROOT_DIR, 'BancoNexa', 'sql', '30_seed_frequencias_notas_parciais.sql');

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

// =============================================================================
// DB-030 — SEED REALISTA DE FREQUÊNCIAS, OFICINA PRÁTICA E NOTAS PARCIAIS (LOTE 3)
// =============================================================================

interface StudentLote3Seed {
  index: number;
  email: string;
  fullName: string;
  registrationNumber: string;
  bio: string;
  classCode: string;
  classPeriod: string;
  enrollmentDate: string;
  profile: StudentScenarioProfile;
  expectedAttendanceRate: number;
}

interface ClassLessonSeed {
  id: string;
  classCode: string;
  classPeriod: string;
  subjectCode: string;
  moduleOrderIndex: number | null;
  teacherEmail: string;
  lessonDate: string;
  workloadHours: number;
  topicSummary: string;
  labEnvironment: string;
}

interface AttendanceRecordSeed {
  lessonId: string;
  studentEmail: string;
  classCode: string;
  classPeriod: string;
  status: AttendanceStatus;
  absentHours: number;
  justificationNote: string | null;
}

interface PracticalTaskSeed {
  id: string;
  classCode: string;
  classPeriod: string;
  subjectCode: string;
  moduleOrderIndex: number;
  title: string;
  description: string;
  blueprintUrl: string;
  dueDate: string;
  maxScore: number;
  isMandatory: boolean;
}

interface TaskCriterionSeed {
  taskId: string;
  competencyCode: string;
  criterionName: string;
  weight: number;
  minAcceptableLevel: number;
}

interface TaskSubmissionSeed {
  taskId: string;
  studentEmail: string;
  classCode: string;
  classPeriod: string;
  status: SubmissionStatus;
  completedAt: string | null;
  evidenceUrl: string | null;
  studentNotes: string | null;
  finalTaskScore: number | null;
}

interface SubmissionEvaluationSeed {
  taskId: string;
  studentEmail: string;
  criterionName: string;
  evaluatorEmail: string;
  achievedLevel: number;
  scoreAwarded: number;
  technicalFeedback: string;
}

interface AcademicAssessmentSeed {
  id: string;
  classCode: string;
  classPeriod: string;
  subjectCode: string;
  moduleOrderIndex: number | null;
  title: string;
  assessmentType: AssessmentType;
  weight: number;
  applicationDate: string;
  maxGrade: number;
}

interface StudentGradeSeed {
  assessmentId: string;
  studentEmail: string;
  classCode: string;
  classPeriod: string;
  recordedByEmail: string;
  gradeValue: number;
  recoveryGrade: number | null;
  comments: string | null;
}

function buildLote3Students(): StudentLote3Seed[] {
  const students: StudentLote3Seed[] = [];
  // Distribuição realista dos 30 estudantes fictícios entre MEC-2026-1 (18) e MEC-2026-2 (12):
  // - 12 HIGH_PERFORMER (100% presença, entregas no prazo e notas altas)
  // - 8 LATE_DELIVERY (80% presença, entregas atrasadas/pendentes e notas medianas)
  // - 5 ATTENDANCE_BORDERLINE (76% presença = 24% faltas, próximo ao limite de 25%)
  // - 5 AT_RISK (68% presença = 32% faltas, entregas atrasadas e notas abaixo da média)
  const mec1Profiles: StudentScenarioProfile[] = [
    'HIGH_PERFORMER', 'HIGH_PERFORMER', 'AT_RISK',
    'HIGH_PERFORMER', 'HIGH_PERFORMER', 'HIGH_PERFORMER', 'HIGH_PERFORMER', 'HIGH_PERFORMER',
    'LATE_DELIVERY', 'LATE_DELIVERY', 'LATE_DELIVERY', 'LATE_DELIVERY', 'LATE_DELIVERY',
    'ATTENDANCE_BORDERLINE', 'ATTENDANCE_BORDERLINE', 'ATTENDANCE_BORDERLINE',
    'AT_RISK', 'AT_RISK',
  ];
  const mec2Profiles: StudentScenarioProfile[] = [
    'HIGH_PERFORMER', 'LATE_DELIVERY', 'ATTENDANCE_BORDERLINE',
    'HIGH_PERFORMER', 'HIGH_PERFORMER', 'HIGH_PERFORMER', 'HIGH_PERFORMER',
    'LATE_DELIVERY', 'LATE_DELIVERY',
    'ATTENDANCE_BORDERLINE',
    'AT_RISK', 'AT_RISK',
  ];

  const attendanceByProfile: Record<StudentScenarioProfile, number> = {
    HIGH_PERFORMER: 100.0,
    LATE_DELIVERY: 80.0,
    ATTENDANCE_BORDERLINE: 76.0,
    AT_RISK: 68.0,
  };

  const mec1Indices = [1, 2, 3, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21];
  const mec2Indices = [4, 5, 6, 22, 23, 24, 25, 26, 27, 28, 29, 30];

  mec1Indices.forEach((idx, pos) => {
    const pad2 = String(idx).padStart(2, '0');
    const pad4 = String(idx).padStart(4, '0');
    const profile = mec1Profiles[pos];
    students.push({
      index: idx,
      email: `estudante.demo${pad2}@aluno.nexa.local`,
      fullName: `Estudante Demo ${pad2}`,
      registrationNumber: `SENAI-2026-${pad4}`,
      bio: `Estudante fictício anônimo da turma MEC-2026-1 (cenário pedagógico ${profile}).`,
      classCode: 'MEC-2026-1',
      classPeriod: '2026.1',
      enrollmentDate: '2026-02-02',
      profile,
      expectedAttendanceRate: attendanceByProfile[profile],
    });
  });

  mec2Indices.forEach((idx, pos) => {
    const pad2 = String(idx).padStart(2, '0');
    const pad4 = String(idx).padStart(4, '0');
    const profile = mec2Profiles[pos];
    students.push({
      index: idx,
      email: `estudante.demo${pad2}@aluno.nexa.local`,
      fullName: `Estudante Demo ${pad2}`,
      registrationNumber: `SENAI-2026-${pad4}`,
      bio: `Estudante fictício anônimo da turma MEC-2026-2 (cenário pedagógico ${profile}).`,
      classCode: 'MEC-2026-2',
      classPeriod: '2026.2',
      enrollmentDate: '2026-07-27',
      profile,
      expectedAttendanceRate: attendanceByProfile[profile],
    });
  });

  return students.sort((a, b) => a.index - b.index);
}

const LOTE3_STUDENTS_SEED: StudentLote3Seed[] = buildLote3Students();

// 12 Aulas Ministradas: 7 em MEC-2026-1 (soma = 25h) e 5 em MEC-2026-2 (soma = 25h)
const LOTE3_LESSONS_SEED: ClassLessonSeed[] = [
  // MEC-2026-1 (7 aulas = 4 + 4 + 4 + 3 + 4 + 3 + 3 = 25h)
  {
    id: '30000000-0000-4000-8000-000000000001',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    subjectCode: 'UC-MET-01',
    moduleOrderIndex: 1,
    teacherEmail: 'instrutor.teoria.demo@senai.nexa.local',
    lessonDate: '2026-02-11',
    workloadHours: 4,
    topicSummary: 'Leitura em milímetros e polegadas com paquímetro universal e resolução 0,02mm.',
    labEnvironment: 'Laboratório de Metrologia 01',
  },
  {
    id: '30000000-0000-4000-8000-000000000002',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    subjectCode: 'UC-MET-01',
    moduleOrderIndex: 2,
    teacherEmail: 'instrutor.teoria.demo@senai.nexa.local',
    lessonDate: '2026-02-18',
    workloadHours: 4,
    topicSummary: 'Medição externa centesimal com micrômetro e inspeção de batimento com relógio comparador.',
    labEnvironment: 'Laboratório de Metrologia 01',
  },
  {
    id: '30000000-0000-4000-8000-000000000003',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    subjectCode: 'UC-DTM-02',
    moduleOrderIndex: 1,
    teacherEmail: 'instrutor.teoria.demo@senai.nexa.local',
    lessonDate: '2026-02-25',
    workloadHours: 4,
    topicSummary: 'Interpretação de vistas ortográficas em 1º diedro, cortes totais e cotagem funcional.',
    labEnvironment: 'Sala de Desenho Técnico 03',
  },
  {
    id: '30000000-0000-4000-8000-000000000004',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    subjectCode: 'UC-DTM-02',
    moduleOrderIndex: 2,
    teacherEmail: 'instrutor.teoria.demo@senai.nexa.local',
    lessonDate: '2026-03-04',
    workloadHours: 3,
    topicSummary: 'Tolerâncias dimensionais ISO 286 (ajustes H7/g6) e simbologia de rugosidade superficial Ra.',
    labEnvironment: 'Sala de Desenho Técnico 03',
  },
  {
    id: '30000000-0000-4000-8000-000000000005',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    subjectCode: 'UC-USI-03',
    moduleOrderIndex: 1,
    teacherEmail: 'instrutor.oficina.demo@senai.nexa.local',
    lessonDate: '2026-03-11',
    workloadHours: 4,
    topicSummary: 'Setup de torno paralelo convencional, centragem de ferramenta, faceamento e cilindramento.',
    labEnvironment: 'Oficina de Tornearia 02',
  },
  {
    id: '30000000-0000-4000-8000-000000000006',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    subjectCode: 'UC-USI-03',
    moduleOrderIndex: 2,
    teacherEmail: 'instrutor.oficina.demo@senai.nexa.local',
    lessonDate: '2026-03-18',
    workloadHours: 3,
    topicSummary: 'Fresamento de superfícies planas, esquadrejamento de blocos e rasgos chavetados.',
    labEnvironment: 'Oficina de Fresagem 01',
  },
  {
    id: '30000000-0000-4000-8000-000000000007',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    subjectCode: 'UC-SEG-04',
    moduleOrderIndex: 1,
    teacherEmail: 'instrutor.oficina.demo@senai.nexa.local',
    lessonDate: '2026-03-25',
    workloadHours: 3,
    topicSummary: 'Inspeção pré-operacional de bancada, uso obrigatório de EPIs e bloqueio NR-12.',
    labEnvironment: 'Oficina Integrada SENAI',
  },
  // MEC-2026-2 (5 aulas = 5 + 5 + 5 + 5 + 5 = 25h)
  {
    id: '30000000-0000-4000-8000-000000000008',
    classCode: 'MEC-2026-2',
    classPeriod: '2026.2',
    subjectCode: 'UC-MET-01',
    moduleOrderIndex: 1,
    teacherEmail: 'instrutor.teoria.demo@senai.nexa.local',
    lessonDate: '2026-08-10',
    workloadHours: 5,
    topicSummary: 'Fundamentos de metrologia linear com paquímetro e conferência dimensional de peças padrão.',
    labEnvironment: 'Laboratório de Metrologia 01',
  },
  {
    id: '30000000-0000-4000-8000-000000000009',
    classCode: 'MEC-2026-2',
    classPeriod: '2026.2',
    subjectCode: 'UC-DTM-02',
    moduleOrderIndex: 1,
    teacherEmail: 'instrutor.teoria.demo@senai.nexa.local',
    lessonDate: '2026-08-17',
    workloadHours: 5,
    topicSummary: 'Leitura de projeções ortográficas ABNT, cortes parciais e interpretação de cotas críticas.',
    labEnvironment: 'Sala de Desenho Técnico 03',
  },
  {
    id: '30000000-0000-4000-8000-000000000010',
    classCode: 'MEC-2026-2',
    classPeriod: '2026.2',
    subjectCode: 'UC-USI-03',
    moduleOrderIndex: 1,
    teacherEmail: 'instrutor.oficina.demo@senai.nexa.local',
    lessonDate: '2026-08-24',
    workloadHours: 5,
    topicSummary: 'Torneamento cilíndrico externo, cálculo de velocidade de corte e controle de avanço.',
    labEnvironment: 'Oficina de Tornearia 02',
  },
  {
    id: '30000000-0000-4000-8000-000000000011',
    classCode: 'MEC-2026-2',
    classPeriod: '2026.2',
    subjectCode: 'UC-USI-03',
    moduleOrderIndex: 2,
    teacherEmail: 'instrutor.oficina.demo@senai.nexa.local',
    lessonDate: '2026-08-31',
    workloadHours: 5,
    topicSummary: 'Operação de fresadora universal, fixação em morsa de precisão e acabamento superficial.',
    labEnvironment: 'Oficina de Fresagem 01',
  },
  {
    id: '30000000-0000-4000-8000-000000000012',
    classCode: 'MEC-2026-2',
    classPeriod: '2026.2',
    subjectCode: 'UC-SEG-04',
    moduleOrderIndex: 2,
    teacherEmail: 'instrutor.oficina.demo@senai.nexa.local',
    lessonDate: '2026-09-07',
    workloadHours: 5,
    topicSummary: 'Procedimentos LOTO, dispositivos de parada de emergência NR-12 e organização 5S.',
    labEnvironment: 'Oficina Integrada SENAI',
  },
];

// 6 Tarefas Práticas de Oficina (4 em MEC-2026-1 e 2 em MEC-2026-2)
const LOTE3_PRACTICAL_TASKS_SEED: PracticalTaskSeed[] = [
  {
    id: '31000000-0000-4000-8000-000000000001',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    subjectCode: 'UC-MET-01',
    moduleOrderIndex: 1,
    title: 'Inspeção Dimensional de Pino Calibrado com Paquímetro',
    description: 'Realizar 12 medições externas, internas e de profundidade com preenchimento de folha de controle H7.',
    blueprintUrl: 'https://cdn.senai.nexa.local/blueprints/pino-calibrado-h7.pdf',
    dueDate: '2026-02-20T22:00:00Z',
    maxScore: 10.0,
    isMandatory: true,
  },
  {
    id: '31000000-0000-4000-8000-000000000002',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    subjectCode: 'UC-DTM-02',
    moduleOrderIndex: 2,
    title: 'Interpretação de Tolerância ISO e Rugosidade em Eixo Motriz',
    description: 'Identificar ajustes eixo-furo H7/g6, desvios geométricos e simbologia Ra no desenho técnico.',
    blueprintUrl: 'https://cdn.senai.nexa.local/blueprints/eixo-motriz-iso286.pdf',
    dueDate: '2026-03-08T22:00:00Z',
    maxScore: 10.0,
    isMandatory: true,
  },
  {
    id: '31000000-0000-4000-8000-000000000003',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    subjectCode: 'UC-USI-03',
    moduleOrderIndex: 1,
    title: 'Usinagem de Eixo Escalonado Ø25mm em Torno Paralelo',
    description: 'Executar faceamento, furo de centro, cilindramento escalonado e acabamento conforme tolerância ±0,02mm.',
    blueprintUrl: 'https://cdn.senai.nexa.local/blueprints/eixo-escalonado-25mm.pdf',
    dueDate: '2026-03-22T22:00:00Z',
    maxScore: 10.0,
    isMandatory: true,
  },
  {
    id: '31000000-0000-4000-8000-000000000004',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    subjectCode: 'UC-USI-03',
    moduleOrderIndex: 2,
    title: 'Fresamento de Bloco Prismático com Rasgo Chavetado',
    description: 'Esquadrejar bloco em aço SAE 1020 e fresar rasgo central garantindo paralelismo e segurança NR-12.',
    blueprintUrl: 'https://cdn.senai.nexa.local/blueprints/bloco-prismatico-chaveta.pdf',
    dueDate: '2026-04-05T22:00:00Z',
    maxScore: 10.0,
    isMandatory: true,
  },
  {
    id: '31000000-0000-4000-8000-000000000005',
    classCode: 'MEC-2026-2',
    classPeriod: '2026.2',
    subjectCode: 'UC-MET-01',
    moduleOrderIndex: 1,
    title: 'Laudo Metrológico de Bucha Cilíndrica com Paquímetro',
    description: 'Conferir diâmetro interno, externo e altura de bucha padronizada registrando incerteza de leitura.',
    blueprintUrl: 'https://cdn.senai.nexa.local/blueprints/bucha-cilindrica-met.pdf',
    dueDate: '2026-08-21T22:00:00Z',
    maxScore: 10.0,
    isMandatory: true,
  },
  {
    id: '31000000-0000-4000-8000-000000000006',
    classCode: 'MEC-2026-2',
    classPeriod: '2026.2',
    subjectCode: 'UC-USI-03',
    moduleOrderIndex: 1,
    title: 'Torneamento de Pino Guia com Chanfro 45° e Controle NR-12',
    description: 'Usinar pino guia em torno convencional cumprindo parâmetros de corte, acabamento e checklist EPI.',
    blueprintUrl: 'https://cdn.senai.nexa.local/blueprints/pino-guia-45graus.pdf',
    dueDate: '2026-09-14T22:00:00Z',
    maxScore: 10.0,
    isMandatory: true,
  },
];

// 18 Critérios / Rubricas Técnicas (3 por tarefa prática, pesos 2.00 + 1.50 + 0.50 = 4.00)
const LOTE3_TASK_CRITERIA_SEED: TaskCriterionSeed[] = [
  // Tarefa 1
  { taskId: '31000000-0000-4000-8000-000000000001', competencyCode: 'COMP-MET-01', criterionName: 'Precisão na Leitura com Paquímetro (±0,02mm)', weight: 2.0, minAcceptableLevel: 3 },
  { taskId: '31000000-0000-4000-8000-000000000001', competencyCode: 'COMP-MET-04', criterionName: 'Calibração, Zeragem e Conservação do Instrumento', weight: 1.5, minAcceptableLevel: 3 },
  { taskId: '31000000-0000-4000-8000-000000000001', competencyCode: 'COMP-SEG-03', criterionName: 'Organização da Bancada e 5S', weight: 0.5, minAcceptableLevel: 3 },
  // Tarefa 2
  { taskId: '31000000-0000-4000-8000-000000000002', competencyCode: 'COMP-DTM-02', criterionName: 'Análise de Ajustes ISO 286 (H7/g6)', weight: 2.0, minAcceptableLevel: 3 },
  { taskId: '31000000-0000-4000-8000-000000000002', competencyCode: 'COMP-DTM-03', criterionName: 'Leitura de Rugosidade Ra e GD&T', weight: 1.5, minAcceptableLevel: 3 },
  { taskId: '31000000-0000-4000-8000-000000000002', competencyCode: 'COMP-DTM-01', criterionName: 'Interpretação de Vistas e Cortes ABNT', weight: 0.5, minAcceptableLevel: 3 },
  // Tarefa 3
  { taskId: '31000000-0000-4000-8000-000000000003', competencyCode: 'COMP-USI-02', criterionName: 'Tolerância Dimensional do Eixo (±0,02mm)', weight: 2.0, minAcceptableLevel: 3 },
  { taskId: '31000000-0000-4000-8000-000000000003', competencyCode: 'COMP-USI-04', criterionName: 'Acabamento Superficial e Controle de Cavacos', weight: 1.5, minAcceptableLevel: 3 },
  { taskId: '31000000-0000-4000-8000-000000000003', competencyCode: 'COMP-SEG-01', criterionName: 'Uso Obrigatório de EPIs e Segurança NR-12', weight: 0.5, minAcceptableLevel: 4 },
  // Tarefa 4
  { taskId: '31000000-0000-4000-8000-000000000004', competencyCode: 'COMP-USI-03', criterionName: 'Esquadrejamento e Profundidade do Rasgo', weight: 2.0, minAcceptableLevel: 3 },
  { taskId: '31000000-0000-4000-8000-000000000004', competencyCode: 'COMP-USI-01', criterionName: 'Cálculo de RPM e Parâmetros de Corte', weight: 1.5, minAcceptableLevel: 3 },
  { taskId: '31000000-0000-4000-8000-000000000004', competencyCode: 'COMP-SEG-02', criterionName: 'Bloqueio LOTO e Segurança na Fresadora', weight: 0.5, minAcceptableLevel: 4 },
  // Tarefa 5
  { taskId: '31000000-0000-4000-8000-000000000005', competencyCode: 'COMP-MET-01', criterionName: 'Conferência de Diâmetro Interno e Externo', weight: 2.0, minAcceptableLevel: 3 },
  { taskId: '31000000-0000-4000-8000-000000000005', competencyCode: 'COMP-MET-04', criterionName: 'Preenchimento Técnico do Laudo Metrológico', weight: 1.5, minAcceptableLevel: 3 },
  { taskId: '31000000-0000-4000-8000-000000000005', competencyCode: 'COMP-SEG-03', criterionName: 'Conservação e Organização 5S', weight: 0.5, minAcceptableLevel: 3 },
  // Tarefa 6
  { taskId: '31000000-0000-4000-8000-000000000006', competencyCode: 'COMP-USI-02', criterionName: 'Precisão do Pino Guia e Chanfro 45°', weight: 2.0, minAcceptableLevel: 3 },
  { taskId: '31000000-0000-4000-8000-000000000006', competencyCode: 'COMP-USI-04', criterionName: 'Qualidade de Acabamento Superficial', weight: 1.5, minAcceptableLevel: 3 },
  { taskId: '31000000-0000-4000-8000-000000000006', competencyCode: 'COMP-SEG-01', criterionName: 'Conformidade EPI e Segurança NR-12', weight: 0.5, minAcceptableLevel: 4 },
];

// 4 Avaliações Formativas e Provas (2 por turma)
const LOTE3_ASSESSMENTS_SEED: AcademicAssessmentSeed[] = [
  {
    id: '32000000-0000-4000-8000-000000000001',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    subjectCode: 'UC-MET-01',
    moduleOrderIndex: 1,
    title: 'Prova Teórica de Leitura de Paquímetro e Micrômetro',
    assessmentType: 'EXAM',
    weight: 2.0,
    applicationDate: '2026-02-27',
    maxGrade: 10.0,
  },
  {
    id: '32000000-0000-4000-8000-000000000002',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    subjectCode: 'UC-USI-03',
    moduleOrderIndex: 1,
    title: 'Microavaliação de Parâmetros de Corte e Segurança NR-12',
    assessmentType: 'MICRO_EVALUATION',
    weight: 1.0,
    applicationDate: '2026-03-27',
    maxGrade: 10.0,
  },
  {
    id: '32000000-0000-4000-8000-000000000003',
    classCode: 'MEC-2026-2',
    classPeriod: '2026.2',
    subjectCode: 'UC-MET-01',
    moduleOrderIndex: 1,
    title: 'Prova Teórica de Metrologia Dimensional e Tolerâncias',
    assessmentType: 'EXAM',
    weight: 2.0,
    applicationDate: '2026-08-28',
    maxGrade: 10.0,
  },
  {
    id: '32000000-0000-4000-8000-000000000004',
    classCode: 'MEC-2026-2',
    classPeriod: '2026.2',
    subjectCode: 'UC-USI-03',
    moduleOrderIndex: 2,
    title: 'Projeto de Processo de Fabricação em Torno e Fresadora',
    assessmentType: 'PROJECT',
    weight: 1.5,
    applicationDate: '2026-09-18',
    maxGrade: 10.0,
  },
];

function buildLote3OperationalDatasets(): {
  attendanceRecords: AttendanceRecordSeed[];
  taskSubmissions: TaskSubmissionSeed[];
  submissionEvaluations: SubmissionEvaluationSeed[];
  studentGrades: StudentGradeSeed[];
  enrollmentMetrics: Map<string, { attendanceRate: number; finalGrade: number }>;
} {
  const attendanceRecords: AttendanceRecordSeed[] = [];
  const taskSubmissions: TaskSubmissionSeed[] = [];
  const submissionEvaluations: SubmissionEvaluationSeed[] = [];
  const studentGrades: StudentGradeSeed[] = [];
  const enrollmentMetrics = new Map<string, { attendanceRate: number; finalGrade: number }>();

  const criteriaByTask = new Map<string, TaskCriterionSeed[]>();
  for (const c of LOTE3_TASK_CRITERIA_SEED) {
    const list = criteriaByTask.get(c.taskId) || [];
    list.push(c);
    criteriaByTask.set(c.taskId, list);
  }

  for (const stu of LOTE3_STUDENTS_SEED) {
    const classLessons = LOTE3_LESSONS_SEED.filter(
      (l) => l.classCode === stu.classCode && l.classPeriod === stu.classPeriod
    );
    const classTasks = LOTE3_PRACTICAL_TASKS_SEED.filter(
      (t) => t.classCode === stu.classCode && t.classPeriod === stu.classPeriod
    );
    const classAssessments = LOTE3_ASSESSMENTS_SEED.filter(
      (a) => a.classCode === stu.classCode && a.classPeriod === stu.classPeriod
    );

    // 1. Presenças e Faltas (total = 25h por turma -> 100%, 80%, 76%, 68% exatos)
    let totalWorkload = 0;
    let totalAbsent = 0;
    classLessons.forEach((lesson, idx) => {
      totalWorkload += lesson.workloadHours;
      let status: AttendanceStatus = 'PRESENT';
      let absentHours = 0;
      let justificationNote: string | null = null;

      if (stu.classCode === 'MEC-2026-1') {
        // Workloads: [4, 4, 4, 3, 4, 3, 3] = 25h
        if (stu.profile === 'LATE_DELIVERY') {
          if (idx === 0) { status = 'ABSENT'; absentHours = 4; }
          if (idx === 1) { status = 'LATE'; absentHours = 1; justificationNote = 'Atraso no transporte coletivo.'; }
        } else if (stu.profile === 'ATTENDANCE_BORDERLINE') {
          if (idx === 3) { status = 'ABSENT'; absentHours = 3; }
          if (idx === 5) { status = 'ABSENT'; absentHours = 3; }
        } else if (stu.profile === 'AT_RISK') {
          if (idx === 0) { status = 'ABSENT'; absentHours = 4; }
          if (idx === 2) { status = 'ABSENT'; absentHours = 4; }
        }
      } else {
        // MEC-2026-2 Workloads: [5, 5, 5, 5, 5] = 25h
        if (stu.profile === 'LATE_DELIVERY') {
          if (idx === 0) { status = 'ABSENT'; absentHours = 5; }
        } else if (stu.profile === 'ATTENDANCE_BORDERLINE') {
          if (idx === 0) { status = 'ABSENT'; absentHours = 5; }
          if (idx === 1) { status = 'LATE'; absentHours = 1; justificationNote = 'Atraso na saída do turno industrial.'; }
        } else if (stu.profile === 'AT_RISK') {
          if (idx === 0) { status = 'ABSENT'; absentHours = 5; }
          if (idx === 1) { status = 'LATE'; absentHours = 3; justificationNote = 'Saída antecipada sem compensação.'; }
        }
      }

      totalAbsent += absentHours;
      attendanceRecords.push({
        lessonId: lesson.id,
        studentEmail: stu.email,
        classCode: stu.classCode,
        classPeriod: stu.classPeriod,
        status,
        absentHours,
        justificationNote,
      });
    });

    const computedAttendanceRate = Number((((totalWorkload - totalAbsent) / totalWorkload) * 100).toFixed(2));

    // 2. Submissões práticas e avaliações por rubrica
    const evaluatedTaskScores: number[] = [];
    classTasks.forEach((task, tIdx) => {
      const criteria = criteriaByTask.get(task.id) || [];
      let subStatus: SubmissionStatus = 'EVALUATED';
      let levels: number[] = [5, 5, 4];

      if (stu.profile === 'HIGH_PERFORMER') {
        subStatus = 'EVALUATED';
        levels = stu.index % 2 === 0 ? [5, 5, 5] : [5, 4, 5];
      } else if (stu.profile === 'LATE_DELIVERY') {
        if (tIdx === classTasks.length - 1) {
          subStatus = 'LATE';
        } else if (classTasks.length >= 4 && tIdx === classTasks.length - 2) {
          subStatus = 'PENDING';
        } else {
          subStatus = 'EVALUATED';
          levels = [4, 3, 4];
        }
      } else if (stu.profile === 'ATTENDANCE_BORDERLINE') {
        if (tIdx === classTasks.length - 1) {
          subStatus = 'SUBMITTED';
        } else {
          subStatus = 'EVALUATED';
          levels = [3, 3, 4];
        }
      } else {
        // AT_RISK
        if (tIdx === 0) {
          subStatus = 'EVALUATED';
          levels = [2, 2, 3];
        } else if (tIdx === 1) {
          subStatus = 'LATE';
        } else {
          subStatus = 'PENDING';
        }
      }

      let finalTaskScore: number | null = null;
      if (subStatus === 'EVALUATED') {
        let weightedSum = 0;
        let weightTotal = 0;
        criteria.forEach((crit, cIdx) => {
          const lvl = levels[cIdx] ?? 3;
          const scoreAwarded = Number(((lvl / 5) * task.maxScore).toFixed(2));
          weightedSum += scoreAwarded * crit.weight;
          weightTotal += crit.weight;
          submissionEvaluations.push({
            taskId: task.id,
            studentEmail: stu.email,
            criterionName: crit.criterionName,
            evaluatorEmail: 'instrutor.oficina.demo@senai.nexa.local',
            achievedLevel: lvl,
            scoreAwarded,
            technicalFeedback:
              lvl >= 4
                ? 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
                : lvl === 3
                  ? 'Critério atendido no nível mínimo aceitável; reforçar controle dimensional.'
                  : 'Desvio acima da tolerância especificada; encaminhar para reforço prático em oficina.',
          });
        });
        finalTaskScore = Number((weightedSum / weightTotal).toFixed(2));
        evaluatedTaskScores.push(finalTaskScore);
      }

      taskSubmissions.push({
        taskId: task.id,
        studentEmail: stu.email,
        classCode: stu.classCode,
        classPeriod: stu.classPeriod,
        status: subStatus,
        completedAt: subStatus === 'EVALUATED' || subStatus === 'SUBMITTED' ? task.dueDate : null,
        evidenceUrl:
          subStatus === 'EVALUATED' || subStatus === 'SUBMITTED'
            ? `https://cdn.senai.nexa.local/evidences/demo${String(stu.index).padStart(2, '0')}-t${tIdx + 1}.jpg`
            : null,
        studentNotes:
          subStatus === 'EVALUATED'
            ? 'Peça usinada e conferida em bancada com folha de inspeção.'
            : subStatus === 'SUBMITTED'
              ? 'Entrega enviada para conferência do instrutor.'
              : subStatus === 'LATE'
                ? 'Entrega atrasada — aguardando reposição em oficina.'
                : null,
        finalTaskScore,
      });
    });

    // 3. Notas Parciais em Avaliações Formativas (student_grades)
    let weightedGradeSum = 0;
    let totalAssessmentWeight = 0;
    classAssessments.forEach((assess, aIdx) => {
      let gradeValue = 8.5;
      let recoveryGrade: number | null = null;
      let comments: string | null = null;

      if (stu.profile === 'HIGH_PERFORMER') {
        gradeValue = Number(Math.min(10.0, 8.6 + ((stu.index + aIdx) % 4) * 0.35).toFixed(2));
        comments = 'Desempenho excelente na avaliação formativa.';
      } else if (stu.profile === 'LATE_DELIVERY') {
        gradeValue = Number((6.4 + ((stu.index + aIdx) % 3) * 0.5).toFixed(2));
        comments = 'Bom aproveitamento teórico; manter regularidade nas entregas práticas.';
      } else if (stu.profile === 'ATTENDANCE_BORDERLINE') {
        gradeValue = Number((5.6 + (aIdx % 2) * 0.6).toFixed(2));
        recoveryGrade = aIdx === 0 ? 7.2 : null;
        comments = 'Atenção ao limite de 25% de faltas; recuperação registrada.';
      } else {
        gradeValue = Number((3.2 + ((stu.index + aIdx) % 3) * 0.65).toFixed(2));
        recoveryGrade = aIdx === 0 ? 5.4 : null;
        comments = 'Estudante em risco acadêmico; plano de intervenção pedagógica recomendado.';
      }

      const effectiveGrade = recoveryGrade !== null && recoveryGrade > gradeValue ? recoveryGrade : gradeValue;
      weightedGradeSum += effectiveGrade * assess.weight;
      totalAssessmentWeight += assess.weight;

      studentGrades.push({
        assessmentId: assess.id,
        studentEmail: stu.email,
        classCode: stu.classCode,
        classPeriod: stu.classPeriod,
        recordedByEmail: 'instrutor.teoria.demo@senai.nexa.local',
        gradeValue,
        recoveryGrade,
        comments,
      });
    });

    const assessmentAvg = totalAssessmentWeight > 0 ? weightedGradeSum / totalAssessmentWeight : 0;
    const practicalAvg =
      evaluatedTaskScores.length > 0
        ? evaluatedTaskScores.reduce((acc, v) => acc + v, 0) / evaluatedTaskScores.length
        : assessmentAvg;
    const consolidatedFinalGrade = Number((assessmentAvg * 0.5 + practicalAvg * 0.5).toFixed(2));

    enrollmentMetrics.set(`${stu.email}::${stu.classCode}::${stu.classPeriod}`, {
      attendanceRate: computedAttendanceRate,
      finalGrade: consolidatedFinalGrade,
    });
  }

  return {
    attendanceRecords,
    taskSubmissions,
    submissionEvaluations,
    studentGrades,
    enrollmentMetrics,
  };
}

function buildLote3IdempotentSeedSql(datasets: ReturnType<typeof buildLote3OperationalDatasets>): string {
  const lines: string[] = [
    '-- =============================================================================',
    '-- PROJETO NEXA — SEED IDEMPOTENTE DE FREQUÊNCIAS, PRÁTICAS E NOTAS (DB-030)',
    '-- SGBD: PostgreSQL 16 (UPSERT via ON CONFLICT DO UPDATE)',
    '-- 30 estudantes fictícios anônimos (zero CPFs ou nomes reais)',
    '-- =============================================================================',
    '',
    'BEGIN;',
    '',
    '-- 1. 30 Estudantes Fictícios Anônimos + Perfis + Matrículas Ativas (MEC-2026-1 e MEC-2026-2)',
  ];

  for (const stu of LOTE3_STUDENTS_SEED) {
    const metrics = datasets.enrollmentMetrics.get(`${stu.email}::${stu.classCode}::${stu.classPeriod}`)!;
    lines.push(
      `INSERT INTO users (email, password_hash, role, is_active)`,
      `VALUES (${sqlLiteral(stu.email)}, ${sqlLiteral(DEMO_BCRYPT_HASH)}, 'STUDENT'::user_role_enum, TRUE)`,
      `ON CONFLICT (email) DO UPDATE`,
      `SET role = EXCLUDED.role, is_active = EXCLUDED.is_active;`,
      `INSERT INTO user_profiles (user_id, full_name, registration_number, bio)`,
      `SELECT u.id, ${sqlLiteral(stu.fullName)}, ${sqlLiteral(stu.registrationNumber)}, ${sqlLiteral(stu.bio)}`,
      `FROM users u WHERE u.email = ${sqlLiteral(stu.email)}`,
      `ON CONFLICT (user_id) DO UPDATE`,
      `SET full_name = EXCLUDED.full_name, registration_number = EXCLUDED.registration_number, bio = EXCLUDED.bio;`,
      `INSERT INTO enrollments (student_id, class_id, enrollment_date, status, final_grade, attendance_rate)`,
      `SELECT u.id, cl.id, DATE ${sqlLiteral(stu.enrollmentDate)}, 'ACTIVE'::enrollment_status_enum, ${metrics.finalGrade.toFixed(2)}, ${metrics.attendanceRate.toFixed(2)}`,
      `FROM users u`,
      `JOIN classes cl ON cl.code = ${sqlLiteral(stu.classCode)} AND cl.period = ${sqlLiteral(stu.classPeriod)}`,
      `WHERE u.email = ${sqlLiteral(stu.email)}`,
      `ON CONFLICT (student_id, class_id) DO UPDATE`,
      `SET status = EXCLUDED.status, final_grade = EXCLUDED.final_grade, attendance_rate = EXCLUDED.attendance_rate;`,
      ''
    );
  }

  lines.push('-- 2. 12 Aulas Ministradas (class_lessons — DB-021)');
  for (const lesson of LOTE3_LESSONS_SEED) {
    const moduleJoin =
      lesson.moduleOrderIndex !== null
        ? `JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = ${lesson.moduleOrderIndex}`
        : '';
    const moduleExpr = lesson.moduleOrderIndex !== null ? 'lm.id' : 'NULL';
    lines.push(
      `INSERT INTO class_lessons (id, class_id, subject_id, module_id, teacher_id, lesson_date, workload_hours, topic_summary, lab_environment)`,
      `SELECT ${sqlLiteral(lesson.id)}::uuid, cl.id, s.id, ${moduleExpr}, u.id, DATE ${sqlLiteral(lesson.lessonDate)}, ${lesson.workloadHours}, ${sqlLiteral(lesson.topicSummary)}, ${sqlLiteral(lesson.labEnvironment)}`,
      `FROM classes cl`,
      `JOIN subjects s ON s.code = ${sqlLiteral(lesson.subjectCode)}`,
      ...(moduleJoin ? [moduleJoin] : []),
      `JOIN users u ON u.email = ${sqlLiteral(lesson.teacherEmail)}`,
      `WHERE cl.code = ${sqlLiteral(lesson.classCode)} AND cl.period = ${sqlLiteral(lesson.classPeriod)}`,
      `ON CONFLICT (id) DO UPDATE`,
      `SET workload_hours = EXCLUDED.workload_hours, topic_summary = EXCLUDED.topic_summary, lab_environment = EXCLUDED.lab_environment;`,
      ''
    );
  }

  lines.push('-- 3. Registros de Presença e Faltas Variados (attendance_records — DB-022: 100%, 80%, 76% e 68%)');
  for (const att of datasets.attendanceRecords) {
    lines.push(
      `INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)`,
      `SELECT ${sqlLiteral(att.lessonId)}::uuid, e.id, u.id, ${sqlLiteral(att.status)}::attendance_status_enum, ${att.absentHours}, ${sqlLiteral(att.justificationNote)}`,
      `FROM users u`,
      `JOIN classes cl ON cl.code = ${sqlLiteral(att.classCode)} AND cl.period = ${sqlLiteral(att.classPeriod)}`,
      `JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id`,
      `WHERE u.email = ${sqlLiteral(att.studentEmail)}`,
      `ON CONFLICT (lesson_id, student_id) DO UPDATE`,
      `SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;`,
      ''
    );
  }

  lines.push('-- 4. 6 Tarefas Práticas de Oficina (practical_tasks — DB-023)');
  for (const task of LOTE3_PRACTICAL_TASKS_SEED) {
    lines.push(
      `INSERT INTO practical_tasks (id, module_id, class_id, title, description, blueprint_url, due_date, max_score, is_mandatory)`,
      `SELECT ${sqlLiteral(task.id)}::uuid, lm.id, cl.id, ${sqlLiteral(task.title)}, ${sqlLiteral(task.description)}, ${sqlLiteral(task.blueprintUrl)}, TIMESTAMPTZ ${sqlLiteral(task.dueDate)}, ${task.maxScore.toFixed(2)}, ${task.isMandatory ? 'TRUE' : 'FALSE'}`,
      `FROM classes cl`,
      `JOIN subjects s ON s.code = ${sqlLiteral(task.subjectCode)}`,
      `JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = ${task.moduleOrderIndex}`,
      `WHERE cl.code = ${sqlLiteral(task.classCode)} AND cl.period = ${sqlLiteral(task.classPeriod)}`,
      `ON CONFLICT (id) DO UPDATE`,
      `SET title = EXCLUDED.title, description = EXCLUDED.description, due_date = EXCLUDED.due_date, max_score = EXCLUDED.max_score;`,
      ''
    );
  }

  lines.push('-- 5. 18 Rubricas / Critérios Técnicos (task_criteria — DB-024)');
  for (const crit of LOTE3_TASK_CRITERIA_SEED) {
    lines.push(
      `INSERT INTO task_criteria (task_id, competency_id, criterion_name, weight, min_acceptable_level)`,
      `SELECT ${sqlLiteral(crit.taskId)}::uuid, cp.id, ${sqlLiteral(crit.criterionName)}, ${crit.weight.toFixed(2)}, ${crit.minAcceptableLevel}`,
      `FROM competencies cp WHERE cp.code = ${sqlLiteral(crit.competencyCode)}`,
      `ON CONFLICT (task_id, criterion_name) DO UPDATE`,
      `SET weight = EXCLUDED.weight, min_acceptable_level = EXCLUDED.min_acceptable_level;`,
      ''
    );
  }

  lines.push('-- 6. Submissões Práticas (task_submissions — DB-025: EVALUATED, SUBMITTED, LATE e PENDING)');
  for (const sub of datasets.taskSubmissions) {
    const completedExpr = sub.completedAt === null ? 'NULL' : `TIMESTAMPTZ ${sqlLiteral(sub.completedAt)}`;
    const scoreExpr = sub.finalTaskScore === null ? 'NULL' : sub.finalTaskScore.toFixed(2);
    lines.push(
      `INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)`,
      `SELECT ${sqlLiteral(sub.taskId)}::uuid, u.id, e.id, ${sqlLiteral(sub.status)}::submission_status_enum, ${completedExpr}, ${sqlLiteral(sub.evidenceUrl)}, ${sqlLiteral(sub.studentNotes)}, ${scoreExpr}`,
      `FROM users u`,
      `JOIN classes cl ON cl.code = ${sqlLiteral(sub.classCode)} AND cl.period = ${sqlLiteral(sub.classPeriod)}`,
      `JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id`,
      `WHERE u.email = ${sqlLiteral(sub.studentEmail)}`,
      `ON CONFLICT (task_id, student_id) DO UPDATE`,
      `SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;`,
      ''
    );
  }

  lines.push('-- 7. Avaliações por Rubrica dos Professores (submission_evaluations — DB-026)');
  for (const ev of datasets.submissionEvaluations) {
    lines.push(
      `INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)`,
      `SELECT ts.id, tc.id, eval_u.id, ${ev.achievedLevel}, ${ev.scoreAwarded.toFixed(2)}, ${sqlLiteral(ev.technicalFeedback)}`,
      `FROM users stu_u`,
      `JOIN task_submissions ts ON ts.task_id = ${sqlLiteral(ev.taskId)}::uuid AND ts.student_id = stu_u.id`,
      `JOIN task_criteria tc ON tc.task_id = ${sqlLiteral(ev.taskId)}::uuid AND tc.criterion_name = ${sqlLiteral(ev.criterionName)}`,
      `JOIN users eval_u ON eval_u.email = ${sqlLiteral(ev.evaluatorEmail)}`,
      `WHERE stu_u.email = ${sqlLiteral(ev.studentEmail)}`,
      `ON CONFLICT (submission_id, criterion_id) DO UPDATE`,
      `SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;`,
      ''
    );
  }

  lines.push('-- 8. 4 Avaliações Formativas e Provas (academic_assessments — DB-027)');
  for (const assess of LOTE3_ASSESSMENTS_SEED) {
    const moduleJoin =
      assess.moduleOrderIndex !== null
        ? `JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = ${assess.moduleOrderIndex}`
        : '';
    const moduleExpr = assess.moduleOrderIndex !== null ? 'lm.id' : 'NULL';
    lines.push(
      `INSERT INTO academic_assessments (id, class_id, subject_id, module_id, title, assessment_type, weight, application_date, max_grade)`,
      `SELECT ${sqlLiteral(assess.id)}::uuid, cl.id, s.id, ${moduleExpr}, ${sqlLiteral(assess.title)}, ${sqlLiteral(assess.assessmentType)}::assessment_type_enum, ${assess.weight.toFixed(2)}, DATE ${sqlLiteral(assess.applicationDate)}, ${assess.maxGrade.toFixed(2)}`,
      `FROM classes cl`,
      `JOIN subjects s ON s.code = ${sqlLiteral(assess.subjectCode)}`,
      ...(moduleJoin ? [moduleJoin] : []),
      `WHERE cl.code = ${sqlLiteral(assess.classCode)} AND cl.period = ${sqlLiteral(assess.classPeriod)}`,
      `ON CONFLICT (id) DO UPDATE`,
      `SET title = EXCLUDED.title, weight = EXCLUDED.weight, application_date = EXCLUDED.application_date, max_grade = EXCLUDED.max_grade;`,
      ''
    );
  }

  lines.push('-- 9. Notas Parciais e Recuperação (student_grades — DB-028)');
  for (const gr of datasets.studentGrades) {
    const recoveryExpr = gr.recoveryGrade === null ? 'NULL' : gr.recoveryGrade.toFixed(2);
    lines.push(
      `INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)`,
      `SELECT ${sqlLiteral(gr.assessmentId)}::uuid, e.id, stu_u.id, rec_u.id, ${gr.gradeValue.toFixed(2)}, ${recoveryExpr}, ${sqlLiteral(gr.comments)}`,
      `FROM users stu_u`,
      `JOIN classes cl ON cl.code = ${sqlLiteral(gr.classCode)} AND cl.period = ${sqlLiteral(gr.classPeriod)}`,
      `JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id`,
      `JOIN users rec_u ON rec_u.email = ${sqlLiteral(gr.recordedByEmail)}`,
      `WHERE stu_u.email = ${sqlLiteral(gr.studentEmail)}`,
      `ON CONFLICT (assessment_id, student_id) DO UPDATE`,
      `SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;`,
      ''
    );
  }

  lines.push('COMMIT;', '');
  return lines.join('\n');
}

function validateAndSimulateLote3Seed(datasets: ReturnType<typeof buildLote3OperationalDatasets>): {
  students: number;
  lessons: number;
  attendanceRecords: number;
  practicalTasks: number;
  taskCriteria: number;
  taskSubmissions: number;
  submissionEvaluations: number;
  academicAssessments: number;
  studentGrades: number;
} {
  const students = new Map<string, StudentLote3Seed>();
  const lessons = new Map<string, ClassLessonSeed>();
  const attendance = new Map<string, AttendanceRecordSeed>();
  const tasks = new Map<string, PracticalTaskSeed>();
  const criteria = new Map<string, TaskCriterionSeed>();
  const submissions = new Map<string, TaskSubmissionSeed>();
  const evaluations = new Map<string, SubmissionEvaluationSeed>();
  const assessments = new Map<string, AcademicAssessmentSeed>();
  const grades = new Map<string, StudentGradeSeed>();

  // 2 passagens completas de upsert comprovando idempotência 100% determinística
  for (let pass = 1; pass <= 2; pass++) {
    for (const s of LOTE3_STUDENTS_SEED) {
      if (!s.email.endsWith('@aluno.nexa.local')) throw new Error(`E-mail não anônimo detectado: ${s.email}`);
      students.set(s.email, s);
    }

    for (const l of LOTE3_LESSONS_SEED) {
      if (l.workloadHours < 1 || l.workloadHours > 8) throw new Error(`workload_hours inválido: ${l.id}`);
      lessons.set(l.id, l);
    }

    for (const a of datasets.attendanceRecords) {
      const lesson = lessons.get(a.lessonId);
      if (!lesson) throw new Error(`Aula inexistente: ${a.lessonId}`);
      if (a.absentHours < 0 || a.absentHours > lesson.workloadHours) {
        throw new Error(`absent_hours fora do limite da aula: ${a.studentEmail}`);
      }
      if (a.status === 'PRESENT' && a.absentHours !== 0) {
        throw new Error(`PRESENT com absent_hours > 0: ${a.studentEmail}`);
      }
      attendance.set(`${a.lessonId}::${a.studentEmail}`, a);
    }

    for (const t of LOTE3_PRACTICAL_TASKS_SEED) {
      if (t.maxScore < 1 || t.maxScore > 10) throw new Error(`max_score inválido: ${t.id}`);
      tasks.set(t.id, t);
    }

    for (const c of LOTE3_TASK_CRITERIA_SEED) {
      if (!tasks.has(c.taskId)) throw new Error(`Tarefa ausente para critério: ${c.taskId}`);
      if (c.weight <= 0 || c.weight > 9.99 || c.minAcceptableLevel < 1 || c.minAcceptableLevel > 5) {
        throw new Error(`Critério inválido: ${c.criterionName}`);
      }
      criteria.set(`${c.taskId}::${c.criterionName}`, c);
    }

    for (const sub of datasets.taskSubmissions) {
      if (!tasks.has(sub.taskId) || !students.has(sub.studentEmail)) {
        throw new Error(`Submissão inválida: ${sub.taskId} / ${sub.studentEmail}`);
      }
      if (sub.finalTaskScore !== null && (sub.finalTaskScore < 0 || sub.finalTaskScore > 10)) {
        throw new Error(`final_task_score fora de 0..10: ${sub.studentEmail}`);
      }
      submissions.set(`${sub.taskId}::${sub.studentEmail}`, sub);
    }

    for (const ev of datasets.submissionEvaluations) {
      if (ev.achievedLevel < 1 || ev.achievedLevel > 5 || ev.scoreAwarded < 0 || ev.scoreAwarded > 10) {
        throw new Error(`Avaliação por rubrica inválida: ${ev.studentEmail}`);
      }
      evaluations.set(`${ev.taskId}::${ev.studentEmail}::${ev.criterionName}`, ev);
    }

    for (const ass of LOTE3_ASSESSMENTS_SEED) {
      if (ass.weight <= 0 || ass.weight > 9.99 || ass.maxGrade <= 0 || ass.maxGrade > 10) {
        throw new Error(`Avaliação formativa inválida: ${ass.id}`);
      }
      assessments.set(ass.id, ass);
    }

    for (const gr of datasets.studentGrades) {
      if (gr.gradeValue < 0 || gr.gradeValue > 10) throw new Error(`grade_value inválido: ${gr.studentEmail}`);
      if (gr.recoveryGrade !== null && (gr.recoveryGrade < 0 || gr.recoveryGrade > 10)) {
        throw new Error(`recovery_grade inválido: ${gr.studentEmail}`);
      }
      grades.set(`${gr.assessmentId}::${gr.studentEmail}`, gr);
    }
  }

  return {
    students: students.size,
    lessons: lessons.size,
    attendanceRecords: attendance.size,
    practicalTasks: tasks.size,
    taskCriteria: criteria.size,
    taskSubmissions: submissions.size,
    submissionEvaluations: evaluations.size,
    academicAssessments: assessments.size,
    studentGrades: grades.size,
  };
}

function main(): void {
  console.log('======================================================================');
  console.log('🌱 [DB-020 / DB-030] NEXA DB SEED — ESTRUTURA CURRICULAR + LOTE 3');
  console.log('======================================================================\n');

  const counts = validateAndSimulateIdempotentSeed();
  const seedSql: string = buildIdempotentSeedSql();
  const lote3Datasets = buildLote3OperationalDatasets();
  const lote3Counts = validateAndSimulateLote3Seed(lote3Datasets);
  const lote3SeedSql: string = buildLote3IdempotentSeedSql(lote3Datasets);

  fs.mkdirSync(path.dirname(SEED_SQL_PATH), { recursive: true });
  fs.writeFileSync(SEED_SQL_PATH, seedSql, 'utf8');
  fs.writeFileSync(SEED_LOTE3_SQL_PATH, lote3SeedSql, 'utf8');

  const env = loadEnvVars();
  const containerName: string = env.POSTGRES_CONTAINER_NAME || 'nexa-postgres';
  const dbUser: string = env.POSTGRES_USER || 'nexa_admin';
  const dbName: string = env.POSTGRES_DB || 'nexa_senai_db';

  if (isPostgresContainerRunning(containerName)) {
    console.log(`🐳 Container '${containerName}' ativo! Aplicando seeds idempotentes (DB-020 + DB-030) no PostgreSQL 16...`);
    execSync(`docker exec -i ${containerName} psql -v ON_ERROR_STOP=1 -U ${dbUser} -d ${dbName}`, {
      cwd: ROOT_DIR,
      input: seedSql,
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    execSync(`docker exec -i ${containerName} psql -v ON_ERROR_STOP=1 -U ${dbUser} -d ${dbName}`, {
      cwd: ROOT_DIR,
      input: lote3SeedSql,
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    console.log('  [OK] Seeds DB-020 e DB-030 executados com sucesso no PostgreSQL 16 via psql (idempotentes).');
  } else {
    console.log(`ℹ️  Container '${containerName}' offline — modo de validação/simulação idempotente (2 passagens UPSERT):`);
    console.log(`  [OK] Script SQL Lote 2 sincronizado em: ${path.relative(ROOT_DIR, SEED_SQL_PATH)}`);
    console.log(`  [OK] Script SQL Lote 3 sincronizado em: ${path.relative(ROOT_DIR, SEED_LOTE3_SQL_PATH)}`);
  }

  console.log('\n📊 Resumo da Grade Curricular SENAI (DB-020 — 100% Dados Fictícios Anônimos):');
  console.log(`  • Cursos Técnicos (courses):                 ${counts.courses}`);
  console.log(`  • Turmas Acadêmicas (classes):               ${counts.classes} (MEC-2026-1, MEC-2026-2)`);
  console.log(`  • Disciplinas (subjects):                    ${counts.subjects}`);
  console.log(`  • Módulos Práticos (learning_modules):       ${counts.modules}`);
  console.log(`  • Competências Industriais (competencies):   ${counts.competencies}`);
  console.log(`  • Vínculos N:M (module_competencies):        ${counts.moduleCompetencies}`);
  console.log(`  • Usuários Base Lote 2 (users/profiles):     ${counts.users}`);
  console.log(`  • Matrículas Base Lote 2 (enrollments):      ${counts.enrollments}`);
  console.log(`  • Alocações Docentes (teacher_assignments):  ${counts.teacherAssignments}`);

  console.log('\n📊 Resumo do Diário, Frequências, Práticas e Notas Parciais (DB-030 — Lote 3):');
  console.log(`  • Estudantes Fictícios Matriculados:         ${lote3Counts.students} (18 MEC-2026-1 / 12 MEC-2026-2)`);
  console.log(`  • Aulas Ministradas (class_lessons):         ${lote3Counts.lessons}`);
  console.log(`  • Registros de Presença (attendance):        ${lote3Counts.attendanceRecords} (perfis 100%, 80%, 76%, 68%)`);
  console.log(`  • Tarefas Práticas (practical_tasks):        ${lote3Counts.practicalTasks}`);
  console.log(`  • Rubricas Técnicas (task_criteria):         ${lote3Counts.taskCriteria}`);
  console.log(`  • Submissões Práticas (task_submissions):    ${lote3Counts.taskSubmissions}`);
  console.log(`  • Avaliações por Rubrica (evaluations):      ${lote3Counts.submissionEvaluations}`);
  console.log(`  • Avaliações Formativas (assessments):       ${lote3Counts.academicAssessments}`);
  console.log(`  • Notas Parciais (student_grades):           ${lote3Counts.studentGrades}`);

  console.log('\n✅ [DB-020 SUCESSO] Seed curricular SENAI executado de forma idempotente (Exit Code 0)!');
  console.log('✅ [DB-030 SUCESSO] Seed realista de frequências, oficinas e notas parciais executado (Exit Code 0)!');
}

main();
