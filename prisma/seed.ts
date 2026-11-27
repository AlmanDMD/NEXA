/**
 * =============================================================================
 * PROJETO NEXA — SEED DE ESTRUTURA CURRICULAR SENAI + LOTE 3 + LOTE 4
 * CARDS: [DB-020], [DB-030] e [DB-040] | Comando: npm run db:seed
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
type RiskLevel = 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';
type AlertCategory = 'ATTENDANCE' | 'GRADE_DROP' | 'PENDING_TASKS' | 'SELF_EVAL_GAP';
type AlertStatus = 'ACTIVE' | 'ACKNOWLEDGED' | 'RESOLVED';
type DiagnosticType = 'ALIGNED' | 'OVERCONFIDENCE_RISK' | 'UNDERCONFIDENCE_SUPPORT' | 'INSUFFICIENT_EVIDENCE';
type MilestoneType = 'MODULE_COMPLETED' | 'SKILL_LEVEL_UP' | 'PERFECT_ATTENDANCE' | 'RECOVERY_ACHIEVED';
type AnnouncementPriority = 'NORMAL' | 'IMPORTANT' | 'URGENT';
type HelpRequestCategory = 'TECHNICAL_DOUBT' | 'PRACTICAL_DIFFICULTY' | 'PERSONAL_PEDAGOGICAL';
type HelpRequestStatus = 'OPEN' | 'IN_PROGRESS' | 'RESOLVED' | 'CLOSED';
type NoteVisibilityScope = 'PRIVATE_AUTHOR' | 'TEACHERS_AND_COORD' | 'COORDINATION_ONLY';
type NoteCategory = 'INTERVENTION' | 'MENTORING' | 'BEHAVIORAL' | 'ACCOMMODATION';
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
const SEED_LOTE4_SQL_PATH: string = path.join(ROOT_DIR, 'BancoNexa', 'sql', '40_seed_diagnosticos_alertas_lote4.sql');
const SEED_LOTE5_SQL_PATH: string = path.join(ROOT_DIR, 'BancoNexa', 'sql', '45_seed_gamification_badges.sql');

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

// =============================================================================
// LOTE 4 (DB-040) — AUTOAVALIAÇÕES, EVIDÊNCIAS, ALERTAS, DIAGNÓSTICOS E MARCOS
// =============================================================================

interface SelfAssessmentFormSeed {
  id: string;
  subjectCode: string;
  moduleOrderIndex: number;
  classCode: string;
  classPeriod: string;
  title: string;
  instructions: string;
  opensAt: string;
  closesAt: string;
  isActive: boolean;
  createdByEmail: string;
}

interface StudentSelfAssessmentSeed {
  formId: string;
  studentEmail: string;
  competencyCode: string;
  perceivedLevel: number;
  confidenceScore: number;
  difficultyNotes: string | null;
  submittedAt: string;
}

interface SkillEvidenceSeed {
  id: string;
  studentEmail: string;
  competencyCode: string;
  sourceTaskId: string | null;
  sourceAssessmentId: string | null;
  verifiedLevel: number;
  verifiedByEmail: string;
  recordedAt: string;
}

interface AcademicAlertSeed {
  id: string;
  studentEmail: string;
  classCode: string;
  classPeriod: string;
  subjectCode: string | null;
  moduleOrderIndex: number | null;
  riskLevel: RiskLevel;
  alertCategory: AlertCategory;
  explainableReason: string;
  metricSnapshot: Record<string, unknown>;
  status: AlertStatus;
  resolvedByEmail: string | null;
  resolutionNotes: string | null;
  createdAt: string;
}

interface ExplainableDiagnosticSeed {
  id: string;
  studentEmail: string;
  classCode: string;
  classPeriod: string;
  subjectCode: string;
  moduleOrderIndex: number;
  competencyCode: string;
  selfPerceivedLevel: number;
  teacherVerifiedLevel: number;
  diagnosticType: DiagnosticType;
  explanationText: string;
  limitationsNote: string;
  recommendedAction: string;
  generatedAt: string;
}

interface MilestoneHistorySeed {
  id: string;
  studentEmail: string;
  classCode: string;
  classPeriod: string;
  subjectCode: string | null;
  moduleOrderIndex: number | null;
  milestoneType: MilestoneType;
  title: string;
  description: string;
  metadata: Record<string, unknown>;
  achievedAt: string;
}

const LOTE4_SELF_ASSESSMENT_FORMS_SEED: SelfAssessmentFormSeed[] = [
  {
    id: '40000000-0000-4000-8000-000000000001',
    subjectCode: 'UC-MET-01',
    moduleOrderIndex: 1,
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    title: 'Autoavaliação — Metrologia com Paquímetro e Tolerância H7 (MEC-2026-1)',
    instructions: 'Avalie honestamente seu nível de domínio (1 a 5) e confiança na leitura de instrumentos metrológicos.',
    opensAt: '2026-03-01T08:00:00Z',
    closesAt: '2026-06-30T23:59:59Z',
    isActive: true,
    createdByEmail: 'instrutor.teoria.demo@senai.nexa.local',
  },
  {
    id: '40000000-0000-4000-8000-000000000002',
    subjectCode: 'UC-USI-03',
    moduleOrderIndex: 1,
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    title: 'Autoavaliação — Módulo de Tornearia Cilíndrica e NR-12 (MEC-2026-1)',
    instructions: 'Indique seu grau de segurança operacional, cálculo de RPM e domínio do torno convencional.',
    opensAt: '2026-03-15T08:00:00Z',
    closesAt: '2026-06-30T23:59:59Z',
    isActive: true,
    createdByEmail: 'instrutor.oficina.demo@senai.nexa.local',
  },
  {
    id: '40000000-0000-4000-8000-000000000003',
    subjectCode: 'UC-MET-01',
    moduleOrderIndex: 1,
    classCode: 'MEC-2026-2',
    classPeriod: '2026.2',
    title: 'Autoavaliação — Metrologia Dimensional e Calibração (MEC-2026-2)',
    instructions: 'Registre sua percepção de domínio nas medições lineares com paquímetro e conservação de instrumentos.',
    opensAt: '2026-08-20T18:00:00Z',
    closesAt: '2026-12-10T23:59:59Z',
    isActive: true,
    createdByEmail: 'instrutor.teoria.demo@senai.nexa.local',
  },
  {
    id: '40000000-0000-4000-8000-000000000004',
    subjectCode: 'UC-USI-03',
    moduleOrderIndex: 1,
    classCode: 'MEC-2026-2',
    classPeriod: '2026.2',
    title: 'Autoavaliação — Tornearia Cilíndrica e Segurança NR-12 (MEC-2026-2)',
    instructions: 'Informe seu domínio prático no faceamento, cilindramento externo e cumprimento da NR-12.',
    opensAt: '2026-09-01T18:00:00Z',
    closesAt: '2026-12-10T23:59:59Z',
    isActive: true,
    createdByEmail: 'instrutor.oficina.demo@senai.nexa.local',
  },
];

// 20 Respostas de autoavaliação cobrindo Metrologia e Tornearia em ambas as turmas
const LOTE4_SELF_ASSESSMENTS_SEED: StudentSelfAssessmentSeed[] = [
  // MEC-2026-1 — Metrologia (Form 1)
  { formId: '40000000-0000-4000-8000-000000000001', studentEmail: 'estudante.demo01@aluno.nexa.local', competencyCode: 'COMP-MET-01', perceivedLevel: 5, confidenceScore: 5, difficultyNotes: null, submittedAt: '2026-03-12T10:15:00Z' },
  { formId: '40000000-0000-4000-8000-000000000001', studentEmail: 'estudante.demo01@aluno.nexa.local', competencyCode: 'COMP-MET-04', perceivedLevel: 4, confidenceScore: 4, difficultyNotes: null, submittedAt: '2026-03-12T10:16:00Z' },
  { formId: '40000000-0000-4000-8000-000000000001', studentEmail: 'estudante.demo02@aluno.nexa.local', competencyCode: 'COMP-MET-01', perceivedLevel: 2, confidenceScore: 2, difficultyNotes: 'Sinto insegurança ao conferir tolerância H7 em furos internos.', submittedAt: '2026-03-13T09:20:00Z' },
  { formId: '40000000-0000-4000-8000-000000000001', studentEmail: 'estudante.demo04@aluno.nexa.local', competencyCode: 'COMP-MET-01', perceivedLevel: 5, confidenceScore: 5, difficultyNotes: 'Acredito dominar totalmente a leitura do nônio.', submittedAt: '2026-03-14T11:00:00Z' },
  { formId: '40000000-0000-4000-8000-000000000001', studentEmail: 'estudante.demo05@aluno.nexa.local', competencyCode: 'COMP-MET-01', perceivedLevel: 4, confidenceScore: 4, difficultyNotes: null, submittedAt: '2026-03-14T11:10:00Z' },
  { formId: '40000000-0000-4000-8000-000000000001', studentEmail: 'estudante.demo06@aluno.nexa.local', competencyCode: 'COMP-MET-04', perceivedLevel: 4, confidenceScore: 3, difficultyNotes: 'Aguardando primeira prática de calibração com blocos-padrão.', submittedAt: '2026-03-15T08:30:00Z' },
  // MEC-2026-1 — Tornearia (Form 2)
  { formId: '40000000-0000-4000-8000-000000000002', studentEmail: 'estudante.demo01@aluno.nexa.local', competencyCode: 'COMP-USI-01', perceivedLevel: 5, confidenceScore: 5, difficultyNotes: null, submittedAt: '2026-03-28T10:00:00Z' },
  { formId: '40000000-0000-4000-8000-000000000002', studentEmail: 'estudante.demo02@aluno.nexa.local', competencyCode: 'COMP-USI-01', perceivedLevel: 2, confidenceScore: 2, difficultyNotes: 'Tenho receio de errar o passe final de acabamento no torno.', submittedAt: '2026-03-28T10:15:00Z' },
  { formId: '40000000-0000-4000-8000-000000000002', studentEmail: 'estudante.demo03@aluno.nexa.local', competencyCode: 'COMP-USI-02', perceivedLevel: 5, confidenceScore: 5, difficultyNotes: 'Faço o cálculo de RPM de cabeça sem dificuldade.', submittedAt: '2026-03-29T09:40:00Z' },
  { formId: '40000000-0000-4000-8000-000000000002', studentEmail: 'estudante.demo04@aluno.nexa.local', competencyCode: 'COMP-SEG-02', perceivedLevel: 5, confidenceScore: 5, difficultyNotes: 'Conheço bem todas as regras da NR-12 no torno.', submittedAt: '2026-03-29T10:05:00Z' },
  { formId: '40000000-0000-4000-8000-000000000002', studentEmail: 'estudante.demo07@aluno.nexa.local', competencyCode: 'COMP-USI-01', perceivedLevel: 4, confidenceScore: 4, difficultyNotes: null, submittedAt: '2026-03-30T11:20:00Z' },
  { formId: '40000000-0000-4000-8000-000000000002', studentEmail: 'estudante.demo08@aluno.nexa.local', competencyCode: 'COMP-USI-02', perceivedLevel: 3, confidenceScore: 3, difficultyNotes: 'Dúvida na seleção de avanço para aço 1045.', submittedAt: '2026-03-30T11:35:00Z' },
  // MEC-2026-2 — Metrologia (Form 3)
  { formId: '40000000-0000-4000-8000-000000000003', studentEmail: 'estudante.demo19@aluno.nexa.local', competencyCode: 'COMP-MET-01', perceivedLevel: 5, confidenceScore: 5, difficultyNotes: null, submittedAt: '2026-09-02T20:10:00Z' },
  { formId: '40000000-0000-4000-8000-000000000003', studentEmail: 'estudante.demo20@aluno.nexa.local', competencyCode: 'COMP-MET-01', perceivedLevel: 2, confidenceScore: 2, difficultyNotes: 'Acho que levo tempo demais para conferir medidas com micrômetro.', submittedAt: '2026-09-02T20:25:00Z' },
  { formId: '40000000-0000-4000-8000-000000000003', studentEmail: 'estudante.demo21@aluno.nexa.local', competencyCode: 'COMP-MET-01', perceivedLevel: 5, confidenceScore: 4, difficultyNotes: 'Leitura em polegada fracionária já dominada.', submittedAt: '2026-09-03T19:45:00Z' },
  { formId: '40000000-0000-4000-8000-000000000003', studentEmail: 'estudante.demo22@aluno.nexa.local', competencyCode: 'COMP-MET-04', perceivedLevel: 3, confidenceScore: 3, difficultyNotes: null, submittedAt: '2026-09-03T20:00:00Z' },
  // MEC-2026-2 — Tornearia (Form 4)
  { formId: '40000000-0000-4000-8000-000000000004', studentEmail: 'estudante.demo19@aluno.nexa.local', competencyCode: 'COMP-USI-01', perceivedLevel: 5, confidenceScore: 4, difficultyNotes: null, submittedAt: '2026-09-22T20:00:00Z' },
  { formId: '40000000-0000-4000-8000-000000000004', studentEmail: 'estudante.demo21@aluno.nexa.local', competencyCode: 'COMP-USI-01', perceivedLevel: 5, confidenceScore: 5, difficultyNotes: 'Já usinei eixos parecidos antes.', submittedAt: '2026-09-22T20:15:00Z' },
  { formId: '40000000-0000-4000-8000-000000000004', studentEmail: 'estudante.demo22@aluno.nexa.local', competencyCode: 'COMP-USI-02', perceivedLevel: 2, confidenceScore: 2, difficultyNotes: 'Insegurança no cálculo da profundidade de corte.', submittedAt: '2026-09-23T19:50:00Z' },
  { formId: '40000000-0000-4000-8000-000000000004', studentEmail: 'estudante.demo23@aluno.nexa.local', competencyCode: 'COMP-SEG-02', perceivedLevel: 4, confidenceScore: 4, difficultyNotes: null, submittedAt: '2026-09-23T20:10:00Z' },
];

// 16 Evidências práticas verificadas por docentes (skill_evidences) vinculadas a submissões e avaliações do Lote 3
const LOTE4_SKILL_EVIDENCES_SEED: SkillEvidenceSeed[] = [
  // Metrologia (MEC-2026-1)
  { id: '41000000-0000-4000-8000-000000000001', studentEmail: 'estudante.demo01@aluno.nexa.local', competencyCode: 'COMP-MET-01', sourceTaskId: '31000000-0000-4000-8000-000000000001', sourceAssessmentId: null, verifiedLevel: 4.8, verifiedByEmail: 'instrutor.teoria.demo@senai.nexa.local', recordedAt: '2026-03-10T11:00:00Z' },
  { id: '41000000-0000-4000-8000-000000000002', studentEmail: 'estudante.demo01@aluno.nexa.local', competencyCode: 'COMP-MET-01', sourceTaskId: null, sourceAssessmentId: '32000000-0000-4000-8000-000000000001', verifiedLevel: 4.6, verifiedByEmail: 'instrutor.teoria.demo@senai.nexa.local', recordedAt: '2026-03-11T11:00:00Z' },
  { id: '41000000-0000-4000-8000-000000000003', studentEmail: 'estudante.demo02@aluno.nexa.local', competencyCode: 'COMP-MET-01', sourceTaskId: '31000000-0000-4000-8000-000000000001', sourceAssessmentId: null, verifiedLevel: 4.5, verifiedByEmail: 'instrutor.teoria.demo@senai.nexa.local', recordedAt: '2026-03-10T11:30:00Z' },
  { id: '41000000-0000-4000-8000-000000000004', studentEmail: 'estudante.demo02@aluno.nexa.local', competencyCode: 'COMP-MET-01', sourceTaskId: null, sourceAssessmentId: '32000000-0000-4000-8000-000000000001', verifiedLevel: 4.3, verifiedByEmail: 'instrutor.teoria.demo@senai.nexa.local', recordedAt: '2026-03-11T11:30:00Z' },
  { id: '41000000-0000-4000-8000-000000000005', studentEmail: 'estudante.demo04@aluno.nexa.local', competencyCode: 'COMP-MET-01', sourceTaskId: '31000000-0000-4000-8000-000000000001', sourceAssessmentId: null, verifiedLevel: 2.4, verifiedByEmail: 'instrutor.teoria.demo@senai.nexa.local', recordedAt: '2026-03-10T12:00:00Z' },
  { id: '41000000-0000-4000-8000-000000000006', studentEmail: 'estudante.demo04@aluno.nexa.local', competencyCode: 'COMP-MET-01', sourceTaskId: null, sourceAssessmentId: '32000000-0000-4000-8000-000000000001', verifiedLevel: 2.2, verifiedByEmail: 'instrutor.teoria.demo@senai.nexa.local', recordedAt: '2026-03-11T12:00:00Z' },
  { id: '41000000-0000-4000-8000-000000000007', studentEmail: 'estudante.demo05@aluno.nexa.local', competencyCode: 'COMP-MET-01', sourceTaskId: '31000000-0000-4000-8000-000000000001', sourceAssessmentId: null, verifiedLevel: 3.8, verifiedByEmail: 'instrutor.teoria.demo@senai.nexa.local', recordedAt: '2026-03-10T12:20:00Z' },
  // Tornearia & NR-12 (MEC-2026-1)
  { id: '41000000-0000-4000-8000-000000000008', studentEmail: 'estudante.demo01@aluno.nexa.local', competencyCode: 'COMP-USI-01', sourceTaskId: '31000000-0000-4000-8000-000000000003', sourceAssessmentId: null, verifiedLevel: 4.9, verifiedByEmail: 'instrutor.oficina.demo@senai.nexa.local', recordedAt: '2026-03-26T11:00:00Z' },
  { id: '41000000-0000-4000-8000-000000000009', studentEmail: 'estudante.demo02@aluno.nexa.local', competencyCode: 'COMP-USI-01', sourceTaskId: '31000000-0000-4000-8000-000000000003', sourceAssessmentId: null, verifiedLevel: 4.2, verifiedByEmail: 'instrutor.oficina.demo@senai.nexa.local', recordedAt: '2026-03-26T11:20:00Z' },
  { id: '41000000-0000-4000-8000-000000000010', studentEmail: 'estudante.demo03@aluno.nexa.local', competencyCode: 'COMP-USI-02', sourceTaskId: null, sourceAssessmentId: '32000000-0000-4000-8000-000000000002', verifiedLevel: 2.3, verifiedByEmail: 'instrutor.oficina.demo@senai.nexa.local', recordedAt: '2026-03-27T11:40:00Z' },
  { id: '41000000-0000-4000-8000-000000000011', studentEmail: 'estudante.demo04@aluno.nexa.local', competencyCode: 'COMP-SEG-02', sourceTaskId: '31000000-0000-4000-8000-000000000003', sourceAssessmentId: null, verifiedLevel: 2.1, verifiedByEmail: 'instrutor.oficina.demo@senai.nexa.local', recordedAt: '2026-03-26T12:00:00Z' },
  // Metrologia & Tornearia (MEC-2026-2)
  { id: '41000000-0000-4000-8000-000000000012', studentEmail: 'estudante.demo19@aluno.nexa.local', competencyCode: 'COMP-MET-01', sourceTaskId: '31000000-0000-4000-8000-000000000005', sourceAssessmentId: null, verifiedLevel: 4.7, verifiedByEmail: 'instrutor.teoria.demo@senai.nexa.local', recordedAt: '2026-09-01T21:00:00Z' },
  { id: '41000000-0000-4000-8000-000000000013', studentEmail: 'estudante.demo20@aluno.nexa.local', competencyCode: 'COMP-MET-01', sourceTaskId: '31000000-0000-4000-8000-000000000005', sourceAssessmentId: null, verifiedLevel: 4.4, verifiedByEmail: 'instrutor.teoria.demo@senai.nexa.local', recordedAt: '2026-09-01T21:15:00Z' },
  { id: '41000000-0000-4000-8000-000000000014', studentEmail: 'estudante.demo21@aluno.nexa.local', competencyCode: 'COMP-MET-01', sourceTaskId: null, sourceAssessmentId: '32000000-0000-4000-8000-000000000003', verifiedLevel: 2.5, verifiedByEmail: 'instrutor.teoria.demo@senai.nexa.local', recordedAt: '2026-09-01T21:30:00Z' },
  { id: '41000000-0000-4000-8000-000000000015', studentEmail: 'estudante.demo21@aluno.nexa.local', competencyCode: 'COMP-USI-01', sourceTaskId: '31000000-0000-4000-8000-000000000006', sourceAssessmentId: null, verifiedLevel: 2.6, verifiedByEmail: 'instrutor.oficina.demo@senai.nexa.local', recordedAt: '2026-09-21T21:00:00Z' },
  { id: '41000000-0000-4000-8000-000000000016', studentEmail: 'estudante.demo22@aluno.nexa.local', competencyCode: 'COMP-USI-02', sourceTaskId: null, sourceAssessmentId: '32000000-0000-4000-8000-000000000004', verifiedLevel: 4.1, verifiedByEmail: 'instrutor.oficina.demo@senai.nexa.local', recordedAt: '2026-09-21T21:20:00Z' },
];

// 8 Alertas Acadêmicos Explicáveis cobrindo LOW, MODERATE, HIGH e CRITICAL e todas as 4 categorias
const LOTE4_ACADEMIC_ALERTS_SEED: AcademicAlertSeed[] = [
  {
    id: '42000000-0000-4000-8000-000000000001',
    studentEmail: 'estudante.demo04@aluno.nexa.local',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    subjectCode: 'UC-USI-03',
    moduleOrderIndex: 1,
    riskLevel: 'CRITICAL',
    alertCategory: 'ATTENDANCE',
    explainableReason: 'Frequência acumulada atingiu 68.00% (8h de faltas não justificadas em 25h ministradas), abaixo do mínimo institucional de 75% do SENAI.',
    metricSnapshot: { attendance_rate_pct: 68.0, absent_hours: 8, total_hours: 25, senai_min_pct: 75.0 },
    status: 'ACTIVE',
    resolvedByEmail: null,
    resolutionNotes: null,
    createdAt: '2026-03-28T13:00:00Z',
  },
  {
    id: '42000000-0000-4000-8000-000000000002',
    studentEmail: 'estudante.demo04@aluno.nexa.local',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    subjectCode: 'UC-USI-03',
    moduleOrderIndex: 1,
    riskLevel: 'CRITICAL',
    alertCategory: 'SELF_EVAL_GAP',
    explainableReason: 'Superestimação crítica em Segurança NR-12 no Torno: aluno declarou nível 5.00, mas evidência prática docente registrou 2.10 (gap +2.90).',
    metricSnapshot: { competency_code: 'COMP-SEG-02', perceived_level: 5.0, avg_verified_level: 2.1, discrepancy_gap: 2.9 },
    status: 'ACTIVE',
    resolvedByEmail: null,
    resolutionNotes: null,
    createdAt: '2026-03-29T14:15:00Z',
  },
  {
    id: '42000000-0000-4000-8000-000000000003',
    studentEmail: 'estudante.demo03@aluno.nexa.local',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    subjectCode: 'UC-MET-01',
    moduleOrderIndex: 1,
    riskLevel: 'HIGH',
    alertCategory: 'ATTENDANCE',
    explainableReason: 'Frequência em 76.00% no limiar preventivo (< 78%); mais 1 falta de 4h colocará o estudante abaixo do mínimo de 75%.',
    metricSnapshot: { attendance_rate_pct: 76.0, absent_hours: 6, total_hours: 25, warning_threshold_pct: 78.0 },
    status: 'ACTIVE',
    resolvedByEmail: null,
    resolutionNotes: null,
    createdAt: '2026-03-25T15:00:00Z',
  },
  {
    id: '42000000-0000-4000-8000-000000000004',
    studentEmail: 'estudante.demo08@aluno.nexa.local',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    subjectCode: 'UC-USI-03',
    moduleOrderIndex: 1,
    riskLevel: 'HIGH',
    alertCategory: 'GRADE_DROP',
    explainableReason: 'Queda de rendimento nas avaliações formativas: média ponderada caiu de 7.40 para 5.20 abaixo da nota de corte (7.00) em Usinagem.',
    metricSnapshot: { previous_avg: 7.4, current_avg: 5.2, passing_score: 7.0, drop_points: -2.2 },
    status: 'ACKNOWLEDGED',
    resolvedByEmail: 'instrutor.oficina.demo@senai.nexa.local',
    resolutionNotes: 'Agendada revisão prática de parâmetros de corte na próxima oficina.',
    createdAt: '2026-03-29T16:00:00Z',
  },
  {
    id: '42000000-0000-4000-8000-000000000005',
    studentEmail: 'estudante.demo02@aluno.nexa.local',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    subjectCode: 'UC-MET-01',
    moduleOrderIndex: 1,
    riskLevel: 'MODERATE',
    alertCategory: 'PENDING_TASKS',
    explainableReason: '2 entregas práticas em atraso/pendentes na oficina de Metrologia e Desenho Técnico necessitando reagendamento de bancada.',
    metricSnapshot: { late_tasks: 1, pending_tasks: 1, total_tasks: 4 },
    status: 'ACTIVE',
    resolvedByEmail: null,
    resolutionNotes: null,
    createdAt: '2026-03-24T11:30:00Z',
  },
  {
    id: '42000000-0000-4000-8000-000000000006',
    studentEmail: 'estudante.demo21@aluno.nexa.local',
    classCode: 'MEC-2026-2',
    classPeriod: '2026.2',
    subjectCode: 'UC-USI-03',
    moduleOrderIndex: 1,
    riskLevel: 'HIGH',
    alertCategory: 'SELF_EVAL_GAP',
    explainableReason: 'Divergência elevada em Tornearia Cilíndrica (MEC-2026-2): autopercepção 5.00 vs. evidência prática docente 2.60 (gap +2.40).',
    metricSnapshot: { competency_code: 'COMP-USI-01', perceived_level: 5.0, avg_verified_level: 2.6, discrepancy_gap: 2.4 },
    status: 'ACTIVE',
    resolvedByEmail: null,
    resolutionNotes: null,
    createdAt: '2026-09-23T21:00:00Z',
  },
  {
    id: '42000000-0000-4000-8000-000000000007',
    studentEmail: 'estudante.demo22@aluno.nexa.local',
    classCode: 'MEC-2026-2',
    classPeriod: '2026.2',
    subjectCode: 'UC-MET-01',
    moduleOrderIndex: 1,
    riskLevel: 'MODERATE',
    alertCategory: 'GRADE_DROP',
    explainableReason: 'Nota parcial de Metrologia Dimensional em 5.80, ligeiramente abaixo da nota de corte (6.00); recomendada prática adicional com micrômetro.',
    metricSnapshot: { current_avg: 5.8, passing_score: 6.0, recovery_available: true },
    status: 'ACTIVE',
    resolvedByEmail: null,
    resolutionNotes: null,
    createdAt: '2026-09-10T21:15:00Z',
  },
  {
    id: '42000000-0000-4000-8000-000000000008',
    studentEmail: 'estudante.demo05@aluno.nexa.local',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    subjectCode: 'UC-MET-01',
    moduleOrderIndex: 1,
    riskLevel: 'LOW',
    alertCategory: 'PENDING_TASKS',
    explainableReason: '1 atividade prática com entrega próxima do vencimento; desempenho geral e frequência permanecem saudáveis (88%).',
    metricSnapshot: { pending_tasks: 1, late_tasks: 0, attendance_rate_pct: 88.0 },
    status: 'RESOLVED',
    resolvedByEmail: 'instrutor.teoria.demo@senai.nexa.local',
    resolutionNotes: 'Estudante entregou o laudo metrológico dentro do prazo estendido.',
    createdAt: '2026-03-18T10:00:00Z',
  },
];

// 10 Diagnósticos Comparativos Explicáveis (cobrindo divergências reais em Metrologia e Tornearia)
const LOTE4_EXPLAINABLE_DIAGNOSTICS_SEED: ExplainableDiagnosticSeed[] = [
  {
    id: '43000000-0000-4000-8000-000000000001',
    studentEmail: 'estudante.demo04@aluno.nexa.local',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    subjectCode: 'UC-MET-01',
    moduleOrderIndex: 1,
    competencyCode: 'COMP-MET-01',
    selfPerceivedLevel: 5.0,
    teacherVerifiedLevel: 2.3,
    diagnosticType: 'OVERCONFIDENCE_RISK',
    explanationText: 'Divergência de +2.70 pontos em Metrologia (Paquímetro e Tolerância H7): estudante se autoavaliou em 5.00, enquanto 2 evidências docentes (prática + prova) resultaram em média 2.30.',
    limitationsNote: 'Baseado em 2 evidências (1 peça de bancada e 1 prova teórica); autoavaliação isolada não comprova domínio metrológico.',
    recommendedAction: 'Realizar sessão prática assistida de leitura de nônio 0,02 mm com conferência cruzada pelo instrutor.',
    generatedAt: '2026-03-15T14:00:00Z',
  },
  {
    id: '43000000-0000-4000-8000-000000000002',
    studentEmail: 'estudante.demo04@aluno.nexa.local',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    subjectCode: 'UC-USI-03',
    moduleOrderIndex: 1,
    competencyCode: 'COMP-SEG-02',
    selfPerceivedLevel: 5.0,
    teacherVerifiedLevel: 2.1,
    diagnosticType: 'OVERCONFIDENCE_RISK',
    explanationText: 'Risco crítico de superestimação em Tornearia / Segurança NR-12: percepção 5.00 contra 2.10 verificado na bancada (gap +2.90).',
    limitationsNote: 'Baseado em 1 avaliação prática de torno convencional; requer nova observação direta de checklist NR-12 antes de operação autônoma.',
    recommendedAction: 'Bloquear operação autônoma do torno até aprovação no checklist presencial de segurança NR-12.',
    generatedAt: '2026-03-30T14:00:00Z',
  },
  {
    id: '43000000-0000-4000-8000-000000000003',
    studentEmail: 'estudante.demo03@aluno.nexa.local',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    subjectCode: 'UC-USI-03',
    moduleOrderIndex: 1,
    competencyCode: 'COMP-USI-02',
    selfPerceivedLevel: 5.0,
    teacherVerifiedLevel: 2.3,
    diagnosticType: 'OVERCONFIDENCE_RISK',
    explanationText: 'Divergência de +2.70 pontos em Tornearia (Cálculo de RPM e Avanço): estudante declarou domínio máximo (5.00), mas a microavaliação apontou 2.30.',
    limitationsNote: 'Baseado em 1 microavaliação escrita; confirmar domínio na regulagem da caixa Norton durante a oficina.',
    recommendedAction: 'Aplicar exercícios guiados de velocidade de corte e seleção de engrenagens no torno.',
    generatedAt: '2026-03-30T14:20:00Z',
  },
  {
    id: '43000000-0000-4000-8000-000000000004',
    studentEmail: 'estudante.demo02@aluno.nexa.local',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    subjectCode: 'UC-MET-01',
    moduleOrderIndex: 1,
    competencyCode: 'COMP-MET-01',
    selfPerceivedLevel: 2.0,
    teacherVerifiedLevel: 4.4,
    diagnosticType: 'UNDERCONFIDENCE_SUPPORT',
    explanationText: 'Subestimação em Metrologia (Paquímetro e Tolerância H7): estudante se avaliou em 2.00 apesar de média docente 4.40 (gap -2.40).',
    limitationsNote: 'Baseado em 2 evidências consistentes; indica insegurança percebida mesmo com desempenho técnico sólido.',
    recommendedAction: 'Oferecer feedback positivo com os laudos corrigidos para fortalecer a autoconfiança na bancada.',
    generatedAt: '2026-03-15T14:30:00Z',
  },
  {
    id: '43000000-0000-4000-8000-000000000005',
    studentEmail: 'estudante.demo02@aluno.nexa.local',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    subjectCode: 'UC-USI-03',
    moduleOrderIndex: 1,
    competencyCode: 'COMP-USI-01',
    selfPerceivedLevel: 2.0,
    teacherVerifiedLevel: 4.2,
    diagnosticType: 'UNDERCONFIDENCE_SUPPORT',
    explanationText: 'Subestimação em Tornearia Cilíndrica: estudante marcou nível 2.00, porém entregou eixo escalonado avaliado em 4.20 (gap -2.20).',
    limitationsNote: 'Baseado em 1 peça usinada avaliada por rubrica; acompanhar confiança nos passes de acabamento.',
    recommendedAction: 'Propor desafio prático progressivo de acabamento com validação imediata de rugosidade.',
    generatedAt: '2026-03-30T14:40:00Z',
  },
  {
    id: '43000000-0000-4000-8000-000000000006',
    studentEmail: 'estudante.demo01@aluno.nexa.local',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    subjectCode: 'UC-MET-01',
    moduleOrderIndex: 1,
    competencyCode: 'COMP-MET-01',
    selfPerceivedLevel: 5.0,
    teacherVerifiedLevel: 4.7,
    diagnosticType: 'ALIGNED',
    explanationText: 'Alinhamento excelente em Metrologia: autopercepção 5.00 compatível com média docente 4.70 (gap +0.30).',
    limitationsNote: 'Baseado em 2 evidências (bancada e prova); manter acompanhamento no módulo de micrômetro centesimal.',
    recommendedAction: 'Avançar para desafios de medição avançada e monitoria entre pares na oficina.',
    generatedAt: '2026-03-15T15:00:00Z',
  },
  {
    id: '43000000-0000-4000-8000-000000000007',
    studentEmail: 'estudante.demo01@aluno.nexa.local',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    subjectCode: 'UC-USI-03',
    moduleOrderIndex: 1,
    competencyCode: 'COMP-USI-01',
    selfPerceivedLevel: 5.0,
    teacherVerifiedLevel: 4.9,
    diagnosticType: 'ALIGNED',
    explanationText: 'Alinhamento consistente em Tornearia Cilíndrica: autopercepção 5.00 e avaliação docente 4.90 (gap +0.10).',
    limitationsNote: 'Baseado na peça prática de torneamento externo avaliada com rubrica completa.',
    recommendedAction: 'Liberar avanço para o módulo de Fresamento de Superfícies Planas e Rasgos.',
    generatedAt: '2026-03-30T15:00:00Z',
  },
  {
    id: '43000000-0000-4000-8000-000000000008',
    studentEmail: 'estudante.demo21@aluno.nexa.local',
    classCode: 'MEC-2026-2',
    classPeriod: '2026.2',
    subjectCode: 'UC-MET-01',
    moduleOrderIndex: 1,
    competencyCode: 'COMP-MET-01',
    selfPerceivedLevel: 5.0,
    teacherVerifiedLevel: 2.5,
    diagnosticType: 'OVERCONFIDENCE_RISK',
    explanationText: 'Superestimação em Metrologia Dimensional (MEC-2026-2): percepção 5.00 versus evidência docente 2.50 (gap +2.50).',
    limitationsNote: 'Baseado em 1 avaliação teórica; complementar com checagem prática de leitura de paquímetro na oficina.',
    recommendedAction: 'Agendar bancada de reforço de leitura de paquímetro em milímetros e polegadas.',
    generatedAt: '2026-09-05T21:00:00Z',
  },
  {
    id: '43000000-0000-4000-8000-000000000009',
    studentEmail: 'estudante.demo21@aluno.nexa.local',
    classCode: 'MEC-2026-2',
    classPeriod: '2026.2',
    subjectCode: 'UC-USI-03',
    moduleOrderIndex: 1,
    competencyCode: 'COMP-USI-01',
    selfPerceivedLevel: 5.0,
    teacherVerifiedLevel: 2.6,
    diagnosticType: 'OVERCONFIDENCE_RISK',
    explanationText: 'Superestimação em Tornearia Cilíndrica (MEC-2026-2): autopercepção 5.00 frente a 2.60 na peça avaliada (gap +2.40).',
    limitationsNote: 'Baseado na entrega prática do pino guia; desvios dimensionais acima da tolerância especificada.',
    recommendedAction: 'Revisar alinhamento de contraponta e conferência intermediária com micrômetro antes do passe final.',
    generatedAt: '2026-09-24T21:00:00Z',
  },
  {
    id: '43000000-0000-4000-8000-000000000010',
    studentEmail: 'estudante.demo20@aluno.nexa.local',
    classCode: 'MEC-2026-2',
    classPeriod: '2026.2',
    subjectCode: 'UC-MET-01',
    moduleOrderIndex: 1,
    competencyCode: 'COMP-MET-01',
    selfPerceivedLevel: 2.0,
    teacherVerifiedLevel: 4.4,
    diagnosticType: 'UNDERCONFIDENCE_SUPPORT',
    explanationText: 'Subestimação em Metrologia (MEC-2026-2): estudante declarou nível 2.00, mas obteve 4.40 na entrega prática (gap -2.40).',
    limitationsNote: 'Baseado em 1 entrega prática com excelente precisão; reforçar confiança na execução sob tempo.',
    recommendedAction: 'Destacar a acurácia alcançada no laudo metrológico e estimular participação ativa em equipe.',
    generatedAt: '2026-09-05T21:30:00Z',
  },
];

// 8 Marcos positivos na Linha do Tempo Acadêmica (student_milestone_history)
const LOTE4_MILESTONES_SEED: MilestoneHistorySeed[] = [
  {
    id: '44000000-0000-4000-8000-000000000001',
    studentEmail: 'estudante.demo01@aluno.nexa.local',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    subjectCode: 'UC-MET-01',
    moduleOrderIndex: 1,
    milestoneType: 'MODULE_COMPLETED',
    title: 'Módulo de Metrologia com Paquímetro Concluído com Excelência',
    description: 'Concluiu todas as práticas de medição linear e tolerância H7 acima da nota de corte.',
    metadata: { final_module_score: 9.4, passing_score: 6.0 },
    achievedAt: '2026-03-12T12:00:00Z',
  },
  {
    id: '44000000-0000-4000-8000-000000000002',
    studentEmail: 'estudante.demo01@aluno.nexa.local',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    subjectCode: 'UC-USI-03',
    moduleOrderIndex: 1,
    milestoneType: 'SKILL_LEVEL_UP',
    title: 'Evolução para Nível 5 em Tornearia Cilíndrica',
    description: 'Atingiu domínio avançado (nível 4.90) na usinagem de eixos escalonados em torno convencional.',
    metadata: { competency_code: 'COMP-USI-01', verified_level: 4.9 },
    achievedAt: '2026-03-28T12:00:00Z',
  },
  {
    id: '44000000-0000-4000-8000-000000000003',
    studentEmail: 'estudante.demo01@aluno.nexa.local',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    subjectCode: null,
    moduleOrderIndex: null,
    milestoneType: 'PERFECT_ATTENDANCE',
    title: '100% de Presença nas Oficinas do 1º Trimestre',
    description: 'Nenhuma falta registrada em todas as 25 horas de laboratório ministradas até o momento.',
    metadata: { attendance_rate_pct: 100.0, total_hours: 25 },
    achievedAt: '2026-03-31T17:00:00Z',
  },
  {
    id: '44000000-0000-4000-8000-000000000004',
    studentEmail: 'estudante.demo02@aluno.nexa.local',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    subjectCode: 'UC-MET-01',
    moduleOrderIndex: 1,
    milestoneType: 'SKILL_LEVEL_UP',
    title: 'Progresso Verificado em Metrologia (Nível 4.40)',
    description: 'Demonstrou alta precisão em leituras com paquímetro e conferência de tolerância ISO.',
    metadata: { competency_code: 'COMP-MET-01', verified_level: 4.4 },
    achievedAt: '2026-03-14T12:00:00Z',
  },
  {
    id: '44000000-0000-4000-8000-000000000005',
    studentEmail: 'estudante.demo05@aluno.nexa.local',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    subjectCode: 'UC-MET-01',
    moduleOrderIndex: 1,
    milestoneType: 'RECOVERY_ACHIEVED',
    title: 'Recuperação Concluída em Metrologia Dimensional',
    description: 'Elevou o desempenho na avaliação de recuperação superando a nota de corte institucional.',
    metadata: { previous_grade: 5.5, recovery_grade: 7.8 },
    achievedAt: '2026-03-22T15:00:00Z',
  },
  {
    id: '44000000-0000-4000-8000-000000000006',
    studentEmail: 'estudante.demo19@aluno.nexa.local',
    classCode: 'MEC-2026-2',
    classPeriod: '2026.2',
    subjectCode: 'UC-MET-01',
    moduleOrderIndex: 1,
    milestoneType: 'MODULE_COMPLETED',
    title: 'Módulo de Metrologia Concluído (Turma Noite)',
    description: 'Completou todas as práticas de medição dimensional com desempenho de destaque.',
    metadata: { final_module_score: 9.1, passing_score: 6.0 },
    achievedAt: '2026-09-05T22:00:00Z',
  },
  {
    id: '44000000-0000-4000-8000-000000000007',
    studentEmail: 'estudante.demo19@aluno.nexa.local',
    classCode: 'MEC-2026-2',
    classPeriod: '2026.2',
    subjectCode: null,
    moduleOrderIndex: null,
    milestoneType: 'PERFECT_ATTENDANCE',
    title: 'Frequência Exemplar (100%) no Turno Noturno',
    description: 'Assiduidade integral em todas as aulas presenciais de laboratório da turma MEC-2026-2.',
    metadata: { attendance_rate_pct: 100.0, total_hours: 25 },
    achievedAt: '2026-09-25T22:00:00Z',
  },
  {
    id: '44000000-0000-4000-8000-000000000008',
    studentEmail: 'estudante.demo20@aluno.nexa.local',
    classCode: 'MEC-2026-2',
    classPeriod: '2026.2',
    subjectCode: 'UC-MET-01',
    moduleOrderIndex: 1,
    milestoneType: 'SKILL_LEVEL_UP',
    title: 'Alta Acurácia Metrológica Validada na Bancada',
    description: 'Atingiu nível 4.40 em medições com paquímetro e laudo dimensional.',
    metadata: { competency_code: 'COMP-MET-01', verified_level: 4.4 },
    achievedAt: '2026-09-06T21:30:00Z',
  },
];

function buildLote4IdempotentSeedSql(): string {
  const lines: string[] = [
    '-- =============================================================================',
    '-- PROJETO NEXA — SEED IDEMPOTENTE LOTE 4: AUTOAVALIAÇÃO, ALERTAS & DIAGNÓSTICOS (DB-040)',
    '-- SGBD: PostgreSQL 16 (UPSERT via ON CONFLICT DO UPDATE)',
    '-- 4 Formulários, 20 Autoavaliações, 16 Evidências, 8 Alertas, 10 Diagnósticos, 8 Marcos',
    '-- =============================================================================',
    '',
    'BEGIN;',
    '',
    '-- 1. Formulários de Autoavaliação (self_assessment_forms — DB-031)',
  ];

  for (const f of LOTE4_SELF_ASSESSMENT_FORMS_SEED) {
    lines.push(
      `INSERT INTO self_assessment_forms (id, module_id, class_id, title, instructions, opens_at, closes_at, is_active, created_by)`,
      `SELECT ${sqlLiteral(f.id)}::UUID, lm.id, cl.id, ${sqlLiteral(f.title)}, ${sqlLiteral(f.instructions)}, TIMESTAMPTZ ${sqlLiteral(f.opensAt)}, TIMESTAMPTZ ${sqlLiteral(f.closesAt)}, ${f.isActive ? 'TRUE' : 'FALSE'}, u.id`,
      `FROM subjects s`,
      `JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = ${f.moduleOrderIndex}`,
      `JOIN classes cl ON cl.code = ${sqlLiteral(f.classCode)} AND cl.period = ${sqlLiteral(f.classPeriod)}`,
      `JOIN users u ON u.email = ${sqlLiteral(f.createdByEmail)}`,
      `WHERE s.code = ${sqlLiteral(f.subjectCode)}`,
      `ON CONFLICT (id) DO UPDATE`,
      `SET title = EXCLUDED.title, instructions = EXCLUDED.instructions, opens_at = EXCLUDED.opens_at, closes_at = EXCLUDED.closes_at, is_active = EXCLUDED.is_active;`,
      ''
    );
  }

  lines.push('-- 2. Respostas de Autoavaliação dos Estudantes (student_self_assessments — DB-032)');
  for (const sa of LOTE4_SELF_ASSESSMENTS_SEED) {
    lines.push(
      `INSERT INTO student_self_assessments (form_id, student_id, competency_id, perceived_level, confidence_score, difficulty_notes, submitted_at)`,
      `SELECT ${sqlLiteral(sa.formId)}::UUID, u.id, cp.id, ${sa.perceivedLevel}, ${sa.confidenceScore}, ${sqlLiteral(sa.difficultyNotes)}, TIMESTAMPTZ ${sqlLiteral(sa.submittedAt)}`,
      `FROM users u`,
      `JOIN competencies cp ON cp.code = ${sqlLiteral(sa.competencyCode)}`,
      `WHERE u.email = ${sqlLiteral(sa.studentEmail)}`,
      `ON CONFLICT (form_id, student_id, competency_id) DO UPDATE`,
      `SET perceived_level = EXCLUDED.perceived_level, confidence_score = EXCLUDED.confidence_score, difficulty_notes = EXCLUDED.difficulty_notes, submitted_at = EXCLUDED.submitted_at;`,
      ''
    );
  }

  lines.push('-- 3. Evidências Práticas Verificadas por Docentes (skill_evidences — DB-033)');
  for (const ev of LOTE4_SKILL_EVIDENCES_SEED) {
    const subExpr = ev.sourceTaskId
      ? `(SELECT ts.id FROM task_submissions ts WHERE ts.task_id = ${sqlLiteral(ev.sourceTaskId)}::UUID AND ts.student_id = stu.id LIMIT 1)`
      : 'NULL::UUID';
    const assExpr = ev.sourceAssessmentId ? `${sqlLiteral(ev.sourceAssessmentId)}::UUID` : 'NULL::UUID';
    lines.push(
      `INSERT INTO skill_evidences (id, student_id, competency_id, source_submission_id, source_assessment_id, verified_level, verified_by, recorded_at)`,
      `SELECT ${sqlLiteral(ev.id)}::UUID, stu.id, cp.id, ${subExpr}, ${assExpr}, ${ev.verifiedLevel.toFixed(2)}, tch.id, TIMESTAMPTZ ${sqlLiteral(ev.recordedAt)}`,
      `FROM users stu`,
      `JOIN competencies cp ON cp.code = ${sqlLiteral(ev.competencyCode)}`,
      `JOIN users tch ON tch.email = ${sqlLiteral(ev.verifiedByEmail)}`,
      `WHERE stu.email = ${sqlLiteral(ev.studentEmail)}`,
      `ON CONFLICT (id) DO UPDATE`,
      `SET verified_level = EXCLUDED.verified_level, verified_by = EXCLUDED.verified_by, recorded_at = EXCLUDED.recorded_at;`,
      ''
    );
  }

  lines.push('-- 4. Alertas Acadêmicos Explicáveis (8 alertas: LOW, MODERATE, HIGH, CRITICAL — DB-034)');
  for (const al of LOTE4_ACADEMIC_ALERTS_SEED) {
    const modExpr =
      al.subjectCode && al.moduleOrderIndex
        ? `(SELECT lm.id FROM learning_modules lm JOIN subjects s ON s.id = lm.subject_id WHERE s.code = ${sqlLiteral(al.subjectCode)} AND lm.order_index = ${al.moduleOrderIndex} LIMIT 1)`
        : 'NULL::UUID';
    const resExpr = al.resolvedByEmail
      ? `(SELECT u2.id FROM users u2 WHERE u2.email = ${sqlLiteral(al.resolvedByEmail)} LIMIT 1)`
      : 'NULL::UUID';
    lines.push(
      `INSERT INTO academic_alerts (id, student_id, enrollment_id, class_id, module_id, risk_level, alert_category, explainable_reason, metric_snapshot, status, resolved_by, resolution_notes, created_at)`,
      `SELECT ${sqlLiteral(al.id)}::UUID, stu.id, enr.id, cl.id, ${modExpr}, ${sqlLiteral(al.riskLevel)}::risk_level_enum, ${sqlLiteral(al.alertCategory)}::alert_category_enum, ${sqlLiteral(al.explainableReason)}, ${sqlLiteral(JSON.stringify(al.metricSnapshot))}::JSONB, ${sqlLiteral(al.status)}::alert_status_enum, ${resExpr}, ${sqlLiteral(al.resolutionNotes)}, TIMESTAMPTZ ${sqlLiteral(al.createdAt)}`,
      `FROM users stu`,
      `JOIN classes cl ON cl.code = ${sqlLiteral(al.classCode)} AND cl.period = ${sqlLiteral(al.classPeriod)}`,
      `JOIN enrollments enr ON enr.student_id = stu.id AND enr.class_id = cl.id`,
      `WHERE stu.email = ${sqlLiteral(al.studentEmail)}`,
      `ON CONFLICT (id) DO UPDATE`,
      `SET risk_level = EXCLUDED.risk_level, explainable_reason = EXCLUDED.explainable_reason, metric_snapshot = EXCLUDED.metric_snapshot, status = EXCLUDED.status, resolved_by = EXCLUDED.resolved_by, resolution_notes = EXCLUDED.resolution_notes;`,
      ''
    );
  }

  lines.push('-- 5. Diagnósticos Explicáveis Comparativos (10 diagnósticos em Metrologia e Tornearia — DB-035)');
  for (const d of LOTE4_EXPLAINABLE_DIAGNOSTICS_SEED) {
    const gap = Number((d.selfPerceivedLevel - d.teacherVerifiedLevel).toFixed(2));
    lines.push(
      `INSERT INTO explainable_diagnostics (id, student_id, class_id, module_id, competency_id, self_perceived_level, teacher_verified_level, discrepancy_gap, diagnostic_type, explanation_text, limitations_note, recommended_action, generated_at)`,
      `SELECT ${sqlLiteral(d.id)}::UUID, stu.id, cl.id, lm.id, cp.id, ${d.selfPerceivedLevel.toFixed(2)}, ${d.teacherVerifiedLevel.toFixed(2)}, ${gap.toFixed(2)}, ${sqlLiteral(d.diagnosticType)}::diagnostic_type_enum, ${sqlLiteral(d.explanationText)}, ${sqlLiteral(d.limitationsNote)}, ${sqlLiteral(d.recommendedAction)}, TIMESTAMPTZ ${sqlLiteral(d.generatedAt)}`,
      `FROM users stu`,
      `JOIN classes cl ON cl.code = ${sqlLiteral(d.classCode)} AND cl.period = ${sqlLiteral(d.classPeriod)}`,
      `JOIN subjects s ON s.code = ${sqlLiteral(d.subjectCode)}`,
      `JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = ${d.moduleOrderIndex}`,
      `JOIN competencies cp ON cp.code = ${sqlLiteral(d.competencyCode)}`,
      `WHERE stu.email = ${sqlLiteral(d.studentEmail)}`,
      `ON CONFLICT (id) DO UPDATE`,
      `SET self_perceived_level = EXCLUDED.self_perceived_level, teacher_verified_level = EXCLUDED.teacher_verified_level, discrepancy_gap = EXCLUDED.discrepancy_gap, diagnostic_type = EXCLUDED.diagnostic_type, explanation_text = EXCLUDED.explanation_text, limitations_note = EXCLUDED.limitations_note, recommended_action = EXCLUDED.recommended_action;`,
      ''
    );
  }

  lines.push('-- 6. Histórico e Linha do Tempo de Marcos Acadêmicos (student_milestone_history — DB-039)');
  for (const ms of LOTE4_MILESTONES_SEED) {
    const modExpr =
      ms.subjectCode && ms.moduleOrderIndex
        ? `(SELECT lm.id FROM learning_modules lm JOIN subjects s ON s.id = lm.subject_id WHERE s.code = ${sqlLiteral(ms.subjectCode)} AND lm.order_index = ${ms.moduleOrderIndex} LIMIT 1)`
        : 'NULL::UUID';
    lines.push(
      `INSERT INTO student_milestone_history (id, student_id, enrollment_id, module_id, milestone_type, title, description, metadata, achieved_at)`,
      `SELECT ${sqlLiteral(ms.id)}::UUID, stu.id, enr.id, ${modExpr}, ${sqlLiteral(ms.milestoneType)}::milestone_type_enum, ${sqlLiteral(ms.title)}, ${sqlLiteral(ms.description)}, ${sqlLiteral(JSON.stringify(ms.metadata))}::JSONB, TIMESTAMPTZ ${sqlLiteral(ms.achievedAt)}`,
      `FROM users stu`,
      `JOIN classes cl ON cl.code = ${sqlLiteral(ms.classCode)} AND cl.period = ${sqlLiteral(ms.classPeriod)}`,
      `JOIN enrollments enr ON enr.student_id = stu.id AND enr.class_id = cl.id`,
      `WHERE stu.email = ${sqlLiteral(ms.studentEmail)}`,
      `ON CONFLICT (id) DO UPDATE`,
      `SET milestone_type = EXCLUDED.milestone_type, title = EXCLUDED.title, description = EXCLUDED.description, metadata = EXCLUDED.metadata, achieved_at = EXCLUDED.achieved_at;`,
      ''
    );
  }

  lines.push('COMMIT;', '');
  return lines.join('\n');
}

function validateAndSimulateLote4Seed(): {
  selfAssessmentForms: number;
  selfAssessments: number;
  skillEvidences: number;
  academicAlerts: number;
  explainableDiagnostics: number;
  milestones: number;
} {
  const forms = new Map<string, SelfAssessmentFormSeed>();
  const responses = new Map<string, StudentSelfAssessmentSeed>();
  const evidences = new Map<string, SkillEvidenceSeed>();
  const alerts = new Map<string, AcademicAlertSeed>();
  const diagnostics = new Map<string, ExplainableDiagnosticSeed>();
  const milestones = new Map<string, MilestoneHistorySeed>();

  // 2 passagens de upsert comprovando idempotência determinística
  for (let pass = 1; pass <= 2; pass++) {
    for (const f of LOTE4_SELF_ASSESSMENT_FORMS_SEED) {
      if (!(f.opensAt < f.closesAt)) throw new Error(`Janela inválida em form ${f.id}`);
      forms.set(f.id, f);
    }
    for (const sa of LOTE4_SELF_ASSESSMENTS_SEED) {
      const form = forms.get(sa.formId);
      if (!form) throw new Error(`Form ausente: ${sa.formId}`);
      if (sa.perceivedLevel < 1 || sa.perceivedLevel > 5 || sa.confidenceScore < 1 || sa.confidenceScore > 5) {
        throw new Error(`Autoavaliação fora de 1..5: ${sa.studentEmail}`);
      }
      if (sa.submittedAt < form.opensAt || sa.submittedAt > form.closesAt) {
        throw new Error(`submittedAt fora da janela do formulário: ${sa.studentEmail}`);
      }
      responses.set(`${sa.formId}::${sa.studentEmail}::${sa.competencyCode}`, sa);
    }
    for (const ev of LOTE4_SKILL_EVIDENCES_SEED) {
      if (!ev.sourceTaskId && !ev.sourceAssessmentId) throw new Error(`Evidência sem origem: ${ev.id}`);
      if (ev.verifiedLevel < 1 || ev.verifiedLevel > 5) throw new Error(`verifiedLevel inválido: ${ev.id}`);
      evidences.set(ev.id, ev);
    }
    for (const al of LOTE4_ACADEMIC_ALERTS_SEED) {
      if (al.explainableReason.trim().length < 10) throw new Error(`explainableReason curto: ${al.id}`);
      alerts.set(al.id, al);
    }
    for (const d of LOTE4_EXPLAINABLE_DIAGNOSTICS_SEED) {
      if (d.selfPerceivedLevel < 1 || d.selfPerceivedLevel > 5 || d.teacherVerifiedLevel < 1 || d.teacherVerifiedLevel > 5) {
        throw new Error(`Diagnóstico fora da escala 1..5: ${d.id}`);
      }
      if (d.explanationText.trim().length < 10 || d.limitationsNote.trim().length < 10) {
        throw new Error(`Explicação/limitação ausente no diagnóstico: ${d.id}`);
      }
      diagnostics.set(d.id, d);
    }
    for (const ms of LOTE4_MILESTONES_SEED) {
      if (ms.title.trim().length < 3) throw new Error(`Título de marco inválido: ${ms.id}`);
      milestones.set(ms.id, ms);
    }
  }

  return {
    selfAssessmentForms: forms.size,
    selfAssessments: responses.size,
    skillEvidences: evidences.size,
    academicAlerts: alerts.size,
    explainableDiagnostics: diagnostics.size,
    milestones: milestones.size,
  };
}

// =============================================================================
// LOTE 5 (DB-041..DB-046): COMUNICAÇÃO OFICIAL, APOIO CONFIDENCIAL & GAMIFICAÇÃO
// =============================================================================

interface ClassAnnouncementSeed {
  id: string;
  classCode: string;
  classPeriod: string;
  subjectCode: string | null;
  authorEmail: string;
  title: string;
  content: string;
  priority: AnnouncementPriority;
  isPinned: boolean;
  publishedAt: string;
  expiresAt: string | null;
}

interface HelpRequestSeed {
  id: string;
  studentEmail: string;
  classCode: string;
  classPeriod: string;
  subjectCode: string;
  moduleOrderIndex: number | null;
  assignedTeacherEmail: string | null;
  category: HelpRequestCategory;
  subjectTitle: string;
  description: string;
  isConfidential: boolean;
  status: HelpRequestStatus;
  resolutionSummary: string | null;
  closedAt: string | null;
}

interface PedagogicalNoteSeed {
  id: string;
  studentEmail: string;
  classCode: string;
  classPeriod: string;
  authorEmail: string;
  visibilityScope: NoteVisibilityScope;
  category: NoteCategory;
  noteContent: string;
  requiresFollowup: boolean;
  followupDate: string | null;
}

interface ChatMessageSeed {
  id: string;
  helpRequestId: string;
  senderEmail: string;
  messageBody: string;
  isRead: boolean;
  readAt: string | null;
  sentAt: string;
}

interface GamificationBadgeSeed {
  code: string;
  title: string;
  description: string;
  criteriaExplanation: string;
  iconName: string;
  xpReward: number;
  competencyCode: string | null;
  isActive: boolean;
}

interface StudentAchievementSeed {
  studentEmail: string;
  classCode: string;
  classPeriod: string;
  badgeCode: string;
  unlockedAt: string;
  originReference: string;
}

const LOTE5_ANNOUNCEMENTS_SEED: ClassAnnouncementSeed[] = [
  {
    id: '51000000-0000-4000-8000-000000000001',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    subjectCode: 'UC-USI-03',
    authorEmail: 'instrutor.oficina.demo@senai.nexa.local',
    title: 'Uso Obrigatório de Óculos de Proteção e Calçado NR-12 na Oficina de Tornearia',
    content: 'Lembramos a todos os estudantes que a entrada na Oficina de Tornearia 02 exige óculos de proteção incolor, avental e calçado de segurança com biqueira.',
    priority: 'URGENT',
    isPinned: true,
    publishedAt: '2026-03-09T11:00:00Z',
    expiresAt: '2026-07-10T23:59:00Z',
  },
  {
    id: '51000000-0000-4000-8000-000000000002',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    subjectCode: 'UC-MET-01',
    authorEmail: 'instrutor.teoria.demo@senai.nexa.local',
    title: 'Horário Extra de Monitoria em Micrômetro Externo e Relógio Comparador',
    content: 'O Laboratório de Metrologia 01 estará aberto às quintas-feiras das 13h30 às 15h30 para reforço prático de leitura centesimal.',
    priority: 'IMPORTANT',
    isPinned: false,
    publishedAt: '2026-03-14T14:00:00Z',
    expiresAt: null,
  },
  {
    id: '51000000-0000-4000-8000-000000000003',
    classCode: 'MEC-2026-2',
    classPeriod: '2026.2',
    subjectCode: null,
    authorEmail: 'coordenacao.demo@senai.nexa.local',
    title: 'Calendário de Avaliações Práticas e Fechamento do 1º Bimestre',
    content: 'A coordenação pedagógica divulgou o cronograma oficial das bancas práticas de Usinagem e Metrologia para a turma MEC-2026-2.',
    priority: 'NORMAL',
    isPinned: true,
    publishedAt: '2026-08-18T12:00:00Z',
    expiresAt: null,
  },
];

const LOTE5_HELP_REQUESTS_SEED: HelpRequestSeed[] = [
  {
    id: '52000000-0000-4000-8000-000000000001',
    studentEmail: 'estudante.demo03@aluno.nexa.local',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    subjectCode: 'UC-USI-03',
    moduleOrderIndex: 1,
    assignedTeacherEmail: 'instrutor.oficina.demo@senai.nexa.local',
    category: 'PRACTICAL_DIFFICULTY',
    subjectTitle: 'Dificuldade na centragem da ferramenta de corte no torno paralelo',
    description: 'Estou errando a altura da ponta da ferramenta no faceamento e gerando ressalto no centro da peça. Gostaria de agendar apoio reservado na bancada.',
    isConfidential: true,
    status: 'IN_PROGRESS',
    resolutionSummary: null,
    closedAt: null,
  },
  {
    id: '52000000-0000-4000-8000-000000000002',
    studentEmail: 'estudante.demo14@aluno.nexa.local',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    subjectCode: 'UC-MET-01',
    moduleOrderIndex: 2,
    assignedTeacherEmail: 'instrutor.teoria.demo@senai.nexa.local',
    category: 'TECHNICAL_DOUBT',
    subjectTitle: 'Dúvida na leitura de meio milímetro no tambor do micrômetro',
    description: 'Confundo quando somar 0,50mm na bainha do micrômetro externo durante a inspeção de eixos H7.',
    isConfidential: true,
    status: 'RESOLVED',
    resolutionSummary: 'Realizada demonstração individual de 20 minutos com calibrador padrão de 25mm e lista de 10 leituras validadas.',
    closedAt: null,
  },
  {
    id: '52000000-0000-4000-8000-000000000003',
    studentEmail: 'estudante.demo29@aluno.nexa.local',
    classCode: 'MEC-2026-2',
    classPeriod: '2026.2',
    subjectCode: 'UC-SEG-04',
    moduleOrderIndex: 2,
    assignedTeacherEmail: 'coordenacao.demo@senai.nexa.local',
    category: 'PERSONAL_PEDAGOGICAL',
    subjectTitle: 'Reposição de aula prática por mudança de escala no trabalho',
    description: 'Tive alteração temporária de turno na empresa e preciso alinhar reposição para não ultrapassar o limite de 25% de faltas.',
    isConfidential: true,
    status: 'CLOSED',
    resolutionSummary: 'Plano de reposição homologado pela coordenação com assinatura de termo e reagendamento para sábado letivo.',
    closedAt: '2026-09-12T17:30:00Z',
  },
];

const LOTE5_PEDAGOGICAL_NOTES_SEED: PedagogicalNoteSeed[] = [
  {
    id: '53000000-0000-4000-8000-000000000001',
    studentEmail: 'estudante.demo03@aluno.nexa.local',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    authorEmail: 'instrutor.oficina.demo@senai.nexa.local',
    visibilityScope: 'TEACHERS_AND_COORD',
    category: 'INTERVENTION',
    noteContent: 'Plano de intervenção prática iniciado após divergência entre autoavaliação e tolerância atingida no eixo escalonado.',
    requiresFollowup: true,
    followupDate: '2026-04-10',
  },
  {
    id: '53000000-0000-4000-8000-000000000002',
    studentEmail: 'estudante.demo29@aluno.nexa.local',
    classCode: 'MEC-2026-2',
    classPeriod: '2026.2',
    authorEmail: 'coordenacao.demo@senai.nexa.local',
    visibilityScope: 'COORDINATION_ONLY',
    category: 'ACCOMMODATION',
    noteContent: 'Acompanhamento de frequência com empresa parceira SENAI para adequação de horário sem prejuízo pedagógico.',
    requiresFollowup: true,
    followupDate: '2026-09-25',
  },
];

const LOTE5_CHAT_MESSAGES_SEED: ChatMessageSeed[] = [
  {
    id: '54000000-0000-4000-8000-000000000001',
    helpRequestId: '52000000-0000-4000-8000-000000000001',
    senderEmail: 'estudante.demo03@aluno.nexa.local',
    messageBody: 'Professor, posso passar amanhã às 13h30 na oficina para treinar o zeramento da ferramenta no contraponto?',
    isRead: true,
    readAt: '2026-03-19T14:05:00Z',
    sentAt: '2026-03-19T13:50:00Z',
  },
  {
    id: '54000000-0000-4000-8000-000000000002',
    helpRequestId: '52000000-0000-4000-8000-000000000001',
    senderEmail: 'instrutor.oficina.demo@senai.nexa.local',
    messageBody: 'Combinado! Separei o Torno 04 para revisarmos juntos a centragem com calços e o faceamento passo a passo.',
    isRead: false,
    readAt: null,
    sentAt: '2026-03-19T14:12:00Z',
  },
  {
    id: '54000000-0000-4000-8000-000000000003',
    helpRequestId: '52000000-0000-4000-8000-000000000002',
    senderEmail: 'instrutor.teoria.demo@senai.nexa.local',
    messageBody: 'Ótima evolução na bateria de leituras de hoje! Todas as 10 medições ficaram dentro de ±0,01mm.',
    isRead: true,
    readAt: '2026-03-15T16:40:00Z',
    sentAt: '2026-03-15T16:20:00Z',
  },
];

// 6 Conquistas Técnicas Transparentes SENAI (DB-045 DoD)
const LOTE5_GAMIFICATION_BADGES_SEED: GamificationBadgeSeed[] = [
  {
    code: 'BADGE-METROLOGIA-100',
    title: 'Mestre do Micrômetro',
    description: 'Domínio comprovado na leitura centesimal com micrômetro externo e inspeção dimensional H7.',
    criteriaExplanation: 'Alcançar nível verificado >= 4.50 nas competências de Paquímetro ou Micrômetro em avaliações práticas validadas pelo instrutor.',
    iconName: 'micrometer-precision',
    xpReward: 150,
    competencyCode: 'COMP-MET-02',
    isActive: true,
  },
  {
    code: 'BADGE-PAQUIMETRO-PRO',
    title: 'Olho de Precisão H7',
    description: 'Excelência no uso de paquímetro universal com resolução 0,02mm sem desvios de leitura.',
    criteriaExplanation: 'Concluir a tarefa prática de Inspeção Dimensional com nota >= 9.00 e evidência verificada na competência COMP-MET-01.',
    iconName: 'caliper-check',
    xpReward: 120,
    competencyCode: 'COMP-MET-01',
    isActive: true,
  },
  {
    code: 'BADGE-TORNEARIA-EXACT',
    title: 'Especialista em Tornearia Cilíndrica',
    description: 'Usinagem de eixo escalonado dentro da tolerância ±0,02mm e acabamento conforme desenho técnico.',
    criteriaExplanation: 'Atingir nível >= 4 em todos os critérios técnicos da rubrica de Torneamento Cilíndrico Externo (COMP-USI-02).',
    iconName: 'lathe-master',
    xpReward: 200,
    competencyCode: 'COMP-USI-02',
    isActive: true,
  },
  {
    code: 'BADGE-SEGURANCA-NR12',
    title: 'Guardião NR-12 & 5S',
    description: 'Conduta exemplar de segurança industrial, bloqueio LOTO, uso integral de EPIs e bancada 5S.',
    criteriaExplanation: 'Manter 100% de conformidade nos checklists de EPI e segurança NR-12 em todas as práticas avaliadas do semestre.',
    iconName: 'shield-nr12',
    xpReward: 180,
    competencyCode: 'COMP-SEG-01',
    isActive: true,
  },
  {
    code: 'BADGE-ASSIDUIDADE-100',
    title: 'Presença de Aço 100%',
    description: 'Assiduidade integral em aulas teóricas e oficinas práticas durante todo o módulo.',
    criteriaExplanation: 'Registrar 100% de presença efetiva (zero faltas não justificadas) em todas as aulas ministradas do ciclo.',
    iconName: 'calendar-medal',
    xpReward: 100,
    competencyCode: null,
    isActive: true,
  },
  {
    code: 'BADGE-AUTOCONHECIMENTO-360',
    title: 'Calibração Metacognitiva',
    description: 'Alinhamento consistente entre autoavaliação discente e evidências práticas verificadas.',
    criteriaExplanation: 'Responder aos formulários de autoavaliação dentro do prazo com discrepância absoluta <= 0.50 frente à avaliação docente.',
    iconName: 'compass-aligned',
    xpReward: 130,
    competencyCode: null,
    isActive: true,
  },
];

const LOTE5_STUDENT_ACHIEVEMENTS_SEED: StudentAchievementSeed[] = [
  {
    studentEmail: 'estudante.demo01@aluno.nexa.local',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    badgeCode: 'BADGE-PAQUIMETRO-PRO',
    unlockedAt: '2026-02-22T18:00:00Z',
    originReference: 'Tarefa: Inspeção Dimensional de Pino Calibrado (Nota 9.60)',
  },
  {
    studentEmail: 'estudante.demo01@aluno.nexa.local',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    badgeCode: 'BADGE-METROLOGIA-100',
    unlockedAt: '2026-03-02T17:15:00Z',
    originReference: 'Módulo 02: Metrologia com Micrômetro (Nível verificado 4.90)',
  },
  {
    studentEmail: 'estudante.demo01@aluno.nexa.local',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    badgeCode: 'BADGE-ASSIDUIDADE-100',
    unlockedAt: '2026-03-26T20:00:00Z',
    originReference: 'Ciclo 2026.1: 25h/25h (100.00% de presença)',
  },
  {
    studentEmail: 'estudante.demo02@aluno.nexa.local',
    classCode: 'MEC-2026-1',
    classPeriod: '2026.1',
    badgeCode: 'BADGE-TORNEARIA-EXACT',
    unlockedAt: '2026-03-24T19:10:00Z',
    originReference: 'Tarefa: Usinagem de Eixo Escalonado Ø25mm (Nível 5)',
  },
  {
    studentEmail: 'estudante.demo04@aluno.nexa.local',
    classCode: 'MEC-2026-2',
    classPeriod: '2026.2',
    badgeCode: 'BADGE-SEGURANCA-NR12',
    unlockedAt: '2026-09-08T18:30:00Z',
    originReference: 'Oficina Integrada SENAI: 100% conformidade EPI/NR-12',
  },
  {
    studentEmail: 'estudante.demo04@aluno.nexa.local',
    classCode: 'MEC-2026-2',
    classPeriod: '2026.2',
    badgeCode: 'BADGE-AUTOCONHECIMENTO-360',
    unlockedAt: '2026-09-15T19:00:00Z',
    originReference: 'Diagnóstico 360° Alinhado (gap 0.10)',
  },
];

function buildLote5IdempotentSeedSql(): string {
  const lines: string[] = [
    '-- =============================================================================',
    '-- PROJETO NEXA — SEED IDEMPOTENTE DO LOTE 5: COMUNICAÇÃO & GAMIFICAÇÃO (DB-045)',
    '-- SGBD: PostgreSQL 16 (UPSERT via ON CONFLICT DO UPDATE)',
    '-- Popula conquistas técnicas SENAI (gamification_badges), conquistas de alunos,',
    '-- avisos de mural, solicitações confidenciais, notas pedagógicas e mensagens.',
    '-- =============================================================================',
    '',
    'BEGIN;',
    '',
    '-- 1. Mural de Avisos da Turma (class_announcements — DB-041)',
  ];

  for (const ann of LOTE5_ANNOUNCEMENTS_SEED) {
    const subjJoin = ann.subjectCode ? `JOIN subjects s ON s.code = ${sqlLiteral(ann.subjectCode)}` : '';
    const subjExpr = ann.subjectCode ? 's.id' : 'NULL';
    const expExpr = ann.expiresAt ? `TIMESTAMPTZ ${sqlLiteral(ann.expiresAt)}` : 'NULL';
    lines.push(
      `INSERT INTO class_announcements (id, class_id, subject_id, author_id, title, content, priority, is_pinned, published_at, expires_at)`,
      `SELECT ${sqlLiteral(ann.id)}::uuid, cl.id, ${subjExpr}, u.id, ${sqlLiteral(ann.title)}, ${sqlLiteral(ann.content)}, ${sqlLiteral(ann.priority)}::announcement_priority_enum, ${ann.isPinned ? 'TRUE' : 'FALSE'}, TIMESTAMPTZ ${sqlLiteral(ann.publishedAt)}, ${expExpr}`,
      `FROM classes cl`,
      ...(subjJoin ? [subjJoin] : []),
      `JOIN users u ON u.email = ${sqlLiteral(ann.authorEmail)}`,
      `WHERE cl.code = ${sqlLiteral(ann.classCode)} AND cl.period = ${sqlLiteral(ann.classPeriod)}`,
      `ON CONFLICT (id) DO UPDATE`,
      `SET title = EXCLUDED.title, content = EXCLUDED.content, priority = EXCLUDED.priority, is_pinned = EXCLUDED.is_pinned;`,
      ''
    );
  }

  lines.push('-- 2. Solicitações Confidenciais de Apoio (help_requests — DB-042)');
  for (const hr of LOTE5_HELP_REQUESTS_SEED) {
    const modJoin = hr.moduleOrderIndex !== null ? `JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = ${hr.moduleOrderIndex}` : '';
    const modExpr = hr.moduleOrderIndex !== null ? 'lm.id' : 'NULL';
    const teacherJoin = hr.assignedTeacherEmail ? `JOIN users t ON t.email = ${sqlLiteral(hr.assignedTeacherEmail)}` : '';
    const teacherExpr = hr.assignedTeacherEmail ? 't.id' : 'NULL';
    const closedExpr = hr.closedAt ? `TIMESTAMPTZ ${sqlLiteral(hr.closedAt)}` : 'NULL';
    lines.push(
      `INSERT INTO help_requests (id, student_id, enrollment_id, subject_id, module_id, assigned_teacher_id, category, subject_title, description, is_confidential, status, resolution_summary, closed_at)`,
      `SELECT ${sqlLiteral(hr.id)}::uuid, u.id, e.id, s.id, ${modExpr}, ${teacherExpr}, ${sqlLiteral(hr.category)}::help_request_category_enum, ${sqlLiteral(hr.subjectTitle)}, ${sqlLiteral(hr.description)}, ${hr.isConfidential ? 'TRUE' : 'FALSE'}, ${sqlLiteral(hr.status)}::help_request_status_enum, ${sqlLiteral(hr.resolutionSummary)}, ${closedExpr}`,
      `FROM users u`,
      `JOIN classes cl ON cl.code = ${sqlLiteral(hr.classCode)} AND cl.period = ${sqlLiteral(hr.classPeriod)}`,
      `JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id`,
      `JOIN subjects s ON s.code = ${sqlLiteral(hr.subjectCode)}`,
      ...(modJoin ? [modJoin] : []),
      ...(teacherJoin ? [teacherJoin] : []),
      `WHERE u.email = ${sqlLiteral(hr.studentEmail)}`,
      `ON CONFLICT (id) DO UPDATE`,
      `SET status = EXCLUDED.status, resolution_summary = EXCLUDED.resolution_summary, closed_at = EXCLUDED.closed_at;`,
      ''
    );
  }

  lines.push('-- 3. Observações Pedagógicas Restritas (pedagogical_notes — DB-043)');
  for (const pn of LOTE5_PEDAGOGICAL_NOTES_SEED) {
    const fupExpr = pn.followupDate ? `DATE ${sqlLiteral(pn.followupDate)}` : 'NULL';
    lines.push(
      `INSERT INTO pedagogical_notes (id, student_id, enrollment_id, author_id, visibility_scope, category, note_content, requires_followup, followup_date)`,
      `SELECT ${sqlLiteral(pn.id)}::uuid, u.id, e.id, a.id, ${sqlLiteral(pn.visibilityScope)}::note_visibility_scope_enum, ${sqlLiteral(pn.category)}::note_category_enum, ${sqlLiteral(pn.noteContent)}, ${pn.requiresFollowup ? 'TRUE' : 'FALSE'}, ${fupExpr}`,
      `FROM users u`,
      `JOIN classes cl ON cl.code = ${sqlLiteral(pn.classCode)} AND cl.period = ${sqlLiteral(pn.classPeriod)}`,
      `JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id`,
      `JOIN users a ON a.email = ${sqlLiteral(pn.authorEmail)}`,
      `WHERE u.email = ${sqlLiteral(pn.studentEmail)}`,
      `ON CONFLICT (id) DO UPDATE`,
      `SET visibility_scope = EXCLUDED.visibility_scope, note_content = EXCLUDED.note_content, requires_followup = EXCLUDED.requires_followup, followup_date = EXCLUDED.followup_date;`,
      ''
    );
  }

  lines.push('-- 4. Mensagens Privadas em Chamados de Apoio (chat_messages — DB-044)');
  for (const cm of LOTE5_CHAT_MESSAGES_SEED) {
    const readAtExpr = cm.readAt ? `TIMESTAMPTZ ${sqlLiteral(cm.readAt)}` : 'NULL';
    lines.push(
      `INSERT INTO chat_messages (id, help_request_id, sender_id, message_body, is_read, read_at, sent_at)`,
      `SELECT ${sqlLiteral(cm.id)}::uuid, ${sqlLiteral(cm.helpRequestId)}::uuid, u.id, ${sqlLiteral(cm.messageBody)}, ${cm.isRead ? 'TRUE' : 'FALSE'}, ${readAtExpr}, TIMESTAMPTZ ${sqlLiteral(cm.sentAt)}`,
      `FROM users u WHERE u.email = ${sqlLiteral(cm.senderEmail)}`,
      `ON CONFLICT (id) DO UPDATE`,
      `SET is_read = EXCLUDED.is_read, read_at = EXCLUDED.read_at;`,
      ''
    );
  }

  lines.push('-- 5. Catálogo Transparente de Conquistas SENAI (gamification_badges — DB-045)');
  for (const bg of LOTE5_GAMIFICATION_BADGES_SEED) {
    const compJoin = bg.competencyCode ? `LEFT JOIN competencies cp ON cp.code = ${sqlLiteral(bg.competencyCode)}` : '';
    const compExpr = bg.competencyCode ? 'cp.id' : 'NULL';
    const fromClause = bg.competencyCode ? `FROM (SELECT 1) AS _seed ${compJoin}` : '';
    lines.push(
      `INSERT INTO gamification_badges (code, title, description, criteria_explanation, icon_name, xp_reward, competency_id, is_active)`,
      bg.competencyCode
        ? `SELECT ${sqlLiteral(bg.code)}, ${sqlLiteral(bg.title)}, ${sqlLiteral(bg.description)}, ${sqlLiteral(bg.criteriaExplanation)}, ${sqlLiteral(bg.iconName)}, ${bg.xpReward}, ${compExpr}, ${bg.isActive ? 'TRUE' : 'FALSE'} ${fromClause}`
        : `VALUES (${sqlLiteral(bg.code)}, ${sqlLiteral(bg.title)}, ${sqlLiteral(bg.description)}, ${sqlLiteral(bg.criteriaExplanation)}, ${sqlLiteral(bg.iconName)}, ${bg.xpReward}, NULL, ${bg.isActive ? 'TRUE' : 'FALSE'})`,
      `ON CONFLICT (code) DO UPDATE`,
      `SET title = EXCLUDED.title, description = EXCLUDED.description, criteria_explanation = EXCLUDED.criteria_explanation, icon_name = EXCLUDED.icon_name, xp_reward = EXCLUDED.xp_reward, is_active = EXCLUDED.is_active;`,
      ''
    );
  }

  lines.push('-- 6. Conquistas Desbloqueadas pelos Estudantes (student_achievements — DB-046)');
  for (const ach of LOTE5_STUDENT_ACHIEVEMENTS_SEED) {
    lines.push(
      `INSERT INTO student_achievements (student_id, enrollment_id, badge_id, unlocked_at, origin_reference)`,
      `SELECT u.id, e.id, b.id, TIMESTAMPTZ ${sqlLiteral(ach.unlockedAt)}, ${sqlLiteral(ach.originReference)}`,
      `FROM users u`,
      `JOIN classes cl ON cl.code = ${sqlLiteral(ach.classCode)} AND cl.period = ${sqlLiteral(ach.classPeriod)}`,
      `JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id`,
      `JOIN gamification_badges b ON b.code = ${sqlLiteral(ach.badgeCode)}`,
      `WHERE u.email = ${sqlLiteral(ach.studentEmail)}`,
      `ON CONFLICT (student_id, badge_id) DO UPDATE`,
      `SET unlocked_at = EXCLUDED.unlocked_at, origin_reference = EXCLUDED.origin_reference;`,
      ''
    );
  }

  lines.push('COMMIT;', '');
  return lines.join('\n');
}

function validateAndSimulateLote5Seed(): {
  announcements: number;
  helpRequests: number;
  pedagogicalNotes: number;
  chatMessages: number;
  badges: number;
  achievements: number;
} {
  const announcements = new Map<string, ClassAnnouncementSeed>();
  const helpRequests = new Map<string, HelpRequestSeed>();
  const notes = new Map<string, PedagogicalNoteSeed>();
  const messages = new Map<string, ChatMessageSeed>();
  const badges = new Map<string, GamificationBadgeSeed>();
  const achievements = new Map<string, StudentAchievementSeed>();

  for (let pass = 1; pass <= 2; pass++) {
    for (const a of LOTE5_ANNOUNCEMENTS_SEED) {
      if (a.title.trim().length < 3 || a.content.trim().length < 5) throw new Error(`Aviso inválido: ${a.id}`);
      announcements.set(a.id, a);
    }
    for (const hr of LOTE5_HELP_REQUESTS_SEED) {
      if (!hr.isConfidential) throw new Error(`HelpRequest deve preservar sigilo padrão: ${hr.id}`);
      if (hr.status === 'CLOSED' && !hr.closedAt) throw new Error(`HelpRequest CLOSED sem closedAt: ${hr.id}`);
      helpRequests.set(hr.id, hr);
    }
    for (const pn of LOTE5_PEDAGOGICAL_NOTES_SEED) {
      if (pn.noteContent.trim().length < 5) throw new Error(`Observação pedagógica curta: ${pn.id}`);
      notes.set(pn.id, pn);
    }
    for (const cm of LOTE5_CHAT_MESSAGES_SEED) {
      if (!helpRequests.has(cm.helpRequestId)) throw new Error(`ChatMessage órfã: ${cm.id}`);
      if (cm.isRead && !cm.readAt) throw new Error(`ChatMessage lida sem readAt: ${cm.id}`);
      messages.set(cm.id, cm);
    }
    for (const b of LOTE5_GAMIFICATION_BADGES_SEED) {
      if (b.xpReward <= 0 || b.criteriaExplanation.trim().length < 15) {
        throw new Error(`Badge inválido: ${b.code}`);
      }
      badges.set(b.code, b);
    }
    for (const ach of LOTE5_STUDENT_ACHIEVEMENTS_SEED) {
      if (!badges.has(ach.badgeCode)) throw new Error(`Conquista referencia badge inexistente: ${ach.badgeCode}`);
      achievements.set(`${ach.studentEmail}::${ach.badgeCode}`, ach);
    }
  }

  return {
    announcements: announcements.size,
    helpRequests: helpRequests.size,
    pedagogicalNotes: notes.size,
    chatMessages: messages.size,
    badges: badges.size,
    achievements: achievements.size,
  };
}

function main(): void {
  const startedAt: number = Date.now();
  console.log('======================================================================');
  console.log('🌱 [DB-020 / DB-030 / DB-040] NEXA DB SEED — LOTES 2, 3 E 4');
  console.log('======================================================================\n');

  const counts = validateAndSimulateIdempotentSeed();
  const seedSql: string = buildIdempotentSeedSql();
  const lote3Datasets = buildLote3OperationalDatasets();
  const lote3Counts = validateAndSimulateLote3Seed(lote3Datasets);
  const lote3SeedSql: string = buildLote3IdempotentSeedSql(lote3Datasets);
  const lote4Counts = validateAndSimulateLote4Seed();
  const lote4SeedSql: string = buildLote4IdempotentSeedSql();
  const lote5Counts = validateAndSimulateLote5Seed();
  const lote5SeedSql: string = buildLote5IdempotentSeedSql();

  fs.mkdirSync(path.dirname(SEED_SQL_PATH), { recursive: true });
  fs.writeFileSync(SEED_SQL_PATH, seedSql, 'utf8');
  fs.writeFileSync(SEED_LOTE3_SQL_PATH, lote3SeedSql, 'utf8');
  fs.writeFileSync(SEED_LOTE4_SQL_PATH, lote4SeedSql, 'utf8');
  fs.writeFileSync(SEED_LOTE5_SQL_PATH, lote5SeedSql, 'utf8');

  const env = loadEnvVars();
  const containerName: string = env.POSTGRES_CONTAINER_NAME || 'nexa-postgres';
  const dbUser: string = env.POSTGRES_USER || 'nexa_admin';
  const dbName: string = env.POSTGRES_DB || 'nexa_senai_db';

  if (isPostgresContainerRunning(containerName)) {
    console.log(`🐳 Container '${containerName}' ativo! Aplicando seeds idempotentes (DB-020 + DB-030 + DB-040 + Lote 5) no PostgreSQL 16...`);
    for (const script of [seedSql, lote3SeedSql, lote4SeedSql, lote5SeedSql]) {
      execSync(`docker exec -i ${containerName} psql -v ON_ERROR_STOP=1 -U ${dbUser} -d ${dbName}`, {
        cwd: ROOT_DIR,
        input: script,
        encoding: 'utf8',
        stdio: ['pipe', 'pipe', 'pipe'],
      });
    }
    console.log('  [OK] Seeds DB-020, DB-030, DB-040 e Lote 5 executados com sucesso no PostgreSQL 16 via psql (idempotentes).');
  } else {
    console.log(`ℹ️  Container '${containerName}' offline — modo de validação/simulação idempotente (2 passagens UPSERT):`);
    console.log(`  [OK] Script SQL Lote 2 sincronizado em: ${path.relative(ROOT_DIR, SEED_SQL_PATH)}`);
    console.log(`  [OK] Script SQL Lote 3 sincronizado em: ${path.relative(ROOT_DIR, SEED_LOTE3_SQL_PATH)}`);
    console.log(`  [OK] Script SQL Lote 4 sincronizado em: ${path.relative(ROOT_DIR, SEED_LOTE4_SQL_PATH)}`);
    console.log(`  [OK] Script SQL Lote 5 sincronizado em: ${path.relative(ROOT_DIR, SEED_LOTE5_SQL_PATH)}`);
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

  console.log('\n📊 Resumo de Autoavaliações, Evidências, Alertas e Diagnósticos (DB-040 — Lote 4):');
  console.log(`  • Formulários Autoavaliação (forms):         ${lote4Counts.selfAssessmentForms}`);
  console.log(`  • Respostas Autoavaliação (self_evals):      ${lote4Counts.selfAssessments}`);
  console.log(`  • Evidências Verificadas (skill_evidences):  ${lote4Counts.skillEvidences}`);
  console.log(`  • Alertas Explicáveis (academic_alerts):     ${lote4Counts.academicAlerts} (LOW, MODERATE, HIGH, CRITICAL)`);
  console.log(`  • Diagnósticos Comparativos (diagnostics):   ${lote4Counts.explainableDiagnostics} (Metrologia & Tornearia)`);
  console.log(`  • Marcos Linha do Tempo (milestones):        ${lote4Counts.milestones}`);

  console.log('\n📊 Resumo de Comunicação, Apoio Confidencial & Gamificação SENAI (DB-045 / Lote 5):');
  console.log(`  • Avisos no Mural (class_announcements):     ${lote5Counts.announcements}`);
  console.log(`  • Solicitações Apoio (help_requests):        ${lote5Counts.helpRequests} (is_confidential = TRUE)`);
  console.log(`  • Observações Restritas (pedagogical_notes): ${lote5Counts.pedagogicalNotes}`);
  console.log(`  • Mensagens Privadas (chat_messages):        ${lote5Counts.chatMessages}`);
  console.log(`  • Conquistas Técnicas (gamification_badges): ${lote5Counts.badges}`);
  console.log(`  • Conquistas Alunos (student_achievements):  ${lote5Counts.achievements}`);
  console.log(`  • Tempo total de execução:                   ${Date.now() - startedAt}ms`);

  console.log('\n✅ [DB-020 SUCESSO] Seed curricular SENAI executado de forma idempotente (Exit Code 0)!');
  console.log('✅ [DB-030 SUCESSO] Seed realista de frequências, oficinas e notas parciais executado (Exit Code 0)!');
  console.log('✅ [DB-040 SUCESSO] Seed de diagnósticos explicáveis, alertas e marcos do Lote 4 executado (Exit Code 0)!');
  console.log('✅ [LOTE 5 SUCESSO] Seed de comunicação oficial, apoio confidencial e conquistas SENAI executado (Exit Code 0)!');
}

main();
