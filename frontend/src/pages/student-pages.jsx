import React, { useState } from 'react';
import {
  AlertTriangle,
  Award,
  Bell,
  BookOpen,
  CalendarDays,
  Check,
  CheckCircle2,
  CircleHelp,
  ClipboardList,
  Download,
  FileText,
  Send,
  ShieldCheck,
  Sparkles,
  Star,
  TrendingUp,
} from '../lib/icons';
import { Link } from '../lib/router';
import { useAcademicQueries } from '../context/AcademicContext';
import {
  cx,
  fmt,
  MetricCard,
  OutlineButton,
  PageHeader,
  PriorityBadge,
  StatusBadge,
} from '../components/ui-primitives';

export function StudentDashboardPage() {
  const {
    activeStudent,
    activeStudentId,
    setActiveStudentId,
    students: studentsQuery,
    getStudentProfileById,
    practicalActivities,
    wallPosts,
    badges,
  } = useAcademicQueries();

  const allStudents = studentsQuery.data ?? [];
  const profile = getStudentProfileById(activeStudent.id);
  const subjects = profile?.subjects ?? [];
  const history = profile?.history ?? [];

  const completedPracticals = practicalActivities.filter((act) =>
    act.completedStudentIds.includes(activeStudent.id),
  ).length;
  const unlockedBadges = badges.filter((b) => b.unlocked).length;

  return (
    <main className="animate-rise">
      <PageHeader
        eyebrow={`Portal do Estudante · ${activeStudent.className}`}
        title={`Olá, ${activeStudent.name.split(' ')[0]}.`}
        description="Acompanhe seu desempenho nas disciplinas, sua frequência regimental e as orientações dos seus professores."
        actions={
          <>
            <select
              value={activeStudentId}
              onChange={(e) => setActiveStudentId(e.target.value)}
              className="h-10 rounded-xl border border-slate-200 bg-white px-3 text-xs font-semibold text-slate-700 outline-none focus:border-sky-500"
              data-testid="select-preview-student"
            >
              {allStudents.map((s) => (
                <option key={s.id} value={s.id}>
                  Visualizar aluno: {s.name} ({s.status})
                </option>
              ))}
            </select>
            <Link
              href="/aluno/ajuda"
              className="inline-flex h-10 items-center justify-center gap-2 rounded-xl bg-sky-700 px-3.5 text-sm font-semibold text-white shadow-sm hover:bg-sky-800"
            >
              <CircleHelp size={15} />
              Pedir ajuda ao professor
            </Link>
          </>
        }
      />

      {activeStudent.attendance < 75 && (
        <div className="mb-5 flex items-start gap-3 rounded-2xl border border-red-200 bg-red-50 p-4 text-xs text-red-900">
          <AlertTriangle size={18} className="mt-0.5 shrink-0 text-red-600" />
          <div>
            <strong className="block text-sm font-bold text-red-800">
              Atenção Regimental SENAI: Frequência abaixo de 75% ({activeStudent.attendance}%)
            </strong>
            <p className="mt-1 leading-5">
              Sua assiduidade está abaixo do limite mínimo regimental de 75% exigido para aprovação. Procure seu professor ou envie uma justificativa na aba de suporte.
            </p>
          </div>
        </div>
      )}

      <div className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Minha média geral"
          value={fmt(activeStudent.average)}
          detail={activeStudent.average >= 7 ? 'Acima da meta institucional (7,0)' : 'Em faixa de atenção pedagógica'}
          icon={TrendingUp}
          tone={activeStudent.average >= 7 ? 'green' : 'amber'}
          trend={activeStudent.average >= 7 ? 'up' : 'down'}
        />
        <MetricCard
          label="Minha frequência"
          value={`${activeStudent.attendance}%`}
          detail={activeStudent.attendance >= 75 ? 'Regular · Mínimo exigido: 75%' : 'Abaixo do mínimo de 75%'}
          icon={CalendarDays}
          tone={activeStudent.attendance >= 75 ? 'blue' : 'red'}
          trend={activeStudent.attendance >= 75 ? 'up' : 'down'}
        />
        <MetricCard
          label="Práticas de oficina"
          value={`${completedPracticals} concluídas`}
          detail="Validadas na bancada pelo docente"
          icon={ClipboardList}
          tone="green"
        />
        <MetricCard
          label="Minhas conquistas"
          value={`${unlockedBadges} / ${badges.length}`}
          detail="Insígnias desbloqueadas no ciclo"
          icon={Award}
          tone="amber"
        />
      </div>

      <div className="grid gap-5 xl:grid-cols-[1.2fr_.8fr]">
        <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_2px_8px_rgba(34,64,99,.035)]">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="font-[var(--app-font-serif)] text-lg font-bold text-slate-800">
                Evolução nas avaliações
              </h2>
              <p className="mt-1 text-xs text-slate-500">
                Sua trajetória de notas ao longo das etapas do semestre
              </p>
            </div>
            <StatusBadge status={activeStudent.status} />
          </div>
          <div className="mt-4 h-52">
            <svg viewBox="0 0 700 190" className="h-full w-full overflow-visible" preserveAspectRatio="none">
              <path
                d="M0,145 C90,138 100,126 160,130 S235,110 295,117 S380,84 440,96 S525,72 575,78 S650,46 700,50"
                fill="none"
                stroke="#1889a0"
                strokeWidth="3"
                strokeLinecap="round"
                className="chart-line"
              />
              <path
                d="M0,165 C100,165 110,158 160,159 S240,150 295,153 S380,142 440,144 S530,134 575,136 S650,127 700,129"
                fill="none"
                stroke="#d7e2eb"
                strokeWidth="2"
                strokeDasharray="5 5"
              />
            </svg>
          </div>
          <div className="flex justify-between text-[10px] text-slate-400">
            <span>Diagnóstica</span>
            <span>AV1</span>
            <span>AV2</span>
            <span>Oficina Prática</span>
            <span>Média Atual</span>
          </div>
        </section>

        <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_2px_8px_rgba(34,64,99,.035)]">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="font-[var(--app-font-serif)] text-lg font-bold text-slate-800">
                Minhas disciplinas
              </h2>
              <p className="mt-1 text-xs text-slate-500">Desempenho e presença por unidade curricular</p>
            </div>
            <Link href="/aluno/notas" className="text-xs font-bold text-sky-700 hover:text-sky-900">
              Ver boletim
            </Link>
          </div>
          <div className="space-y-4">
            {subjects.map((sub) => (
              <div key={sub.id}>
                <div className="mb-1.5 flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-700">{sub.name}</span>
                  <span className="font-bold text-slate-800">
                    Média {fmt(sub.average)} · {sub.attendance}% pres.
                  </span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                  <div
                    className={cx(
                      'h-full rounded-full',
                      sub.status === 'Regular'
                        ? 'bg-sky-700'
                        : sub.status === 'Atenção'
                          ? 'bg-amber-400'
                          : 'bg-red-500',
                    )}
                    style={{ width: `${(sub.average / 10) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>

      <div className="mt-5 grid gap-5 xl:grid-cols-[1fr_1fr]">
        <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_2px_8px_rgba(34,64,99,.035)]">
          <h2 className="font-[var(--app-font-serif)] text-lg font-bold text-slate-800">
            Feedbacks e registros dos professores
          </h2>
          <p className="mt-1 text-xs text-slate-500">
            Orientações registradas pelos docentes no seu histórico
          </p>
          <div className="mt-5 space-y-4 border-l border-slate-200 pl-4">
            {history.map((item) => (
              <div key={`${item.date}-${item.title}`} className="relative">
                <span className="absolute -left-[21px] top-1 h-2.5 w-2.5 rounded-full bg-sky-600" />
                <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                  {item.date} · {item.author}
                </p>
                <p className="mt-1 text-sm font-semibold text-slate-700">{item.title}</p>
                <p className="mt-1 text-xs leading-5 text-slate-500">{item.detail}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_2px_8px_rgba(34,64,99,.035)]">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="font-[var(--app-font-serif)] text-lg font-bold text-slate-800">
                Avisos recentes da turma
              </h2>
              <p className="mt-1 text-xs text-slate-500">Comunicados publicados pelos seus professores</p>
            </div>
            <Link href="/aluno/ajuda" className="text-xs font-bold text-sky-700 hover:text-sky-900">
              Abrir mural
            </Link>
          </div>
          <div className="space-y-3">
            {wallPosts.slice(0, 2).map((post) => (
              <div key={post.id} className="rounded-xl border border-slate-100 bg-slate-50/70 p-3.5">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="font-bold text-sky-700">{post.tag}</span>
                  <span className="text-slate-400">{post.date}</span>
                </div>
                <strong className="mt-1 block text-xs font-bold text-slate-800">{post.title}</strong>
                <p className="mt-1 text-xs leading-5 text-slate-600">{post.content}</p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}

export function StudentGradesReportPage() {
  const { activeStudent, getStudentProfileById } = useAcademicQueries();
  const [downloaded, setDownloaded] = useState(false);
  const profile = getStudentProfileById(activeStudent.id);
  const subjects = profile?.subjects ?? [];

  return (
    <main className="animate-rise">
      <PageHeader
        eyebrow={`Boletim Escolar · ${activeStudent.course}`}
        title="Minhas Notas, Frequência e Boletim"
        description="Consulte suas notas detalhadas por avaliação teórica e prática, além do controle regimental de faltas."
        actions={
          <OutlineButton
            icon={Download}
            tone="primary"
            onClick={() => {
              setDownloaded(true);
              setTimeout(() => setDownloaded(false), 3000);
            }}
            testId="button-export-student-report"
          >
            Baixar boletim individual (PDF)
          </OutlineButton>
        }
      />

      {downloaded && (
        <div className="mb-5 flex items-center gap-2 rounded-xl border border-emerald-100 bg-emerald-50 px-4 py-3 text-sm font-semibold text-emerald-800">
          <CheckCircle2 size={17} />
          Boletim individual de {activeStudent.name} (Matrícula #{activeStudent.registration}) gerado com sucesso.
        </div>
      )}

      <div className="mb-6 rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_2px_8px_rgba(34,64,99,.035)]">
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-sky-700">
              Termômetro Regimental SENAI (Mínimo 75% de presença)
            </span>
            <h2 className="mt-1 font-[var(--app-font-serif)] text-lg font-bold text-slate-800">
              Frequência Geral Acumulada: {activeStudent.attendance}%
            </h2>
            <p className="mt-0.5 text-xs text-slate-500">
              {activeStudent.attendance >= 75
                ? 'Você está dentro do índice regimental exigido para certificação nas unidades curriculares.'
                : 'Atenção: frequência abaixo de 75%. Procure a orientação docente para plano de reposição.'}
            </p>
          </div>
          <StatusBadge status={activeStudent.status} />
        </div>
        <div className="mt-4 relative h-3 w-full overflow-hidden rounded-full bg-slate-100">
          <div
            className={cx(
              'h-full rounded-full transition-all',
              activeStudent.attendance < 75
                ? 'bg-red-500'
                : activeStudent.attendance < 82
                  ? 'bg-amber-400'
                  : 'bg-emerald-500',
            )}
            style={{ width: `${activeStudent.attendance}%` }}
          />
        </div>
        <div className="mt-1.5 flex justify-between text-[10px] font-semibold text-slate-400">
          <span>0%</span>
          <span className="text-red-600">Limite mínimo SENAI: 75%</span>
          <span>100%</span>
        </div>
      </div>

      <div className="overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-[0_2px_8px_rgba(34,64,99,.035)]">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[760px] text-left">
            <thead className="border-b border-slate-100 bg-slate-50/70">
              <tr>
                {[
                  'Unidade Curricular / Disciplina',
                  'AV1 (Teórica)',
                  'AV2 (Projeto)',
                  'Oficina Prática',
                  'Média Final',
                  'Frequência',
                  'Faltas',
                  'Situação',
                ].map((head) => (
                  <th
                    key={head}
                    className="px-5 py-3.5 text-[10px] font-bold uppercase tracking-[.09em] text-slate-500"
                  >
                    {head}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {subjects.map((sub) => (
                <tr key={sub.id} className="hover:bg-slate-50/70">
                  <td className="px-5 py-4">
                    <div className="flex items-center gap-3">
                      <span className="rounded-lg bg-sky-50 p-2 text-sky-700">
                        <BookOpen size={15} />
                      </span>
                      <strong className="text-sm text-slate-700">{sub.name}</strong>
                    </div>
                  </td>
                  <td className="px-5 py-4 text-sm text-slate-600">{fmt(sub.av1)}</td>
                  <td className="px-5 py-4 text-sm text-slate-600">{fmt(sub.av2)}</td>
                  <td className="px-5 py-4 text-sm text-slate-600">{fmt(sub.pratica)}</td>
                  <td className="px-5 py-4 text-sm font-bold text-slate-800">{fmt(sub.average)}</td>
                  <td className="px-5 py-4">
                    <span
                      className={cx(
                        'text-sm font-bold',
                        sub.attendance < 75 ? 'text-red-600' : 'text-slate-700',
                      )}
                    >
                      {sub.attendance}%
                    </span>
                  </td>
                  <td className="px-5 py-4 text-xs text-slate-500">
                    {sub.absences} de {sub.totalClasses} aulas
                  </td>
                  <td className="px-5 py-4">
                    <StatusBadge status={sub.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </main>
  );
}

export function StudentSelfAssessmentPage() {
  const { competencies, updateCompetencySelfLevel, badges } = useAcademicQueries();
  const [savedToast, setSavedToast] = useState(false);
  const [reflection, setReflection] = useState(
    'Tenho evoluído bastante na montagem prática em bancada e quero reforçar a velocidade de diagnóstico de falhas.',
  );

  return (
    <main className="animate-rise">
      <PageHeader
        eyebrow="Desenvolvimento & Gamificação"
        title="Autoavaliação & Conquistas"
        description="Avalie sua evolução nas competências técnicas e socioemocionais do SENAI e acompanhe suas insígnias."
        actions={
          <OutlineButton
            icon={CheckCircle2}
            tone="primary"
            onClick={() => {
              setSavedToast(true);
              setTimeout(() => setSavedToast(false), 3000);
            }}
            testId="button-save-self-assessment"
          >
            Salvar autoavaliação
          </OutlineButton>
        }
      />

      {savedToast && (
        <div className="mb-5 flex items-center gap-2 rounded-xl border border-emerald-100 bg-emerald-50 px-4 py-3 text-sm font-semibold text-emerald-800">
          <CheckCircle2 size={17} />
          Autoavaliação enviada com sucesso! Sua reflexão já está visível para o professor responsável.
        </div>
      )}

      <div className="grid gap-5 xl:grid-cols-[1.2fr_.8fr]">
        <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_2px_8px_rgba(34,64,99,.035)]">
          <h2 className="font-[var(--app-font-serif)] text-lg font-bold text-slate-800">
            Matriz de Autoavaliação de Competências (Escala 1 a 5)
          </h2>
          <p className="mt-1 text-xs text-slate-500">
            Selecione o nível que melhor representa seu domínio atual e compare com a avaliação docente.
          </p>

          <div className="mt-5 space-y-5">
            {competencies.map((comp) => (
              <div key={comp.id} className="rounded-xl border border-slate-200/80 bg-slate-50/50 p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="rounded-md bg-sky-50 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-sky-700">
                    {comp.category}
                  </span>
                  <span className="text-xs font-semibold text-slate-500">
                    Avaliação do Professor: <strong className="text-sky-800">Nível {comp.teacherLevel}/5</strong>
                  </span>
                </div>
                <h3 className="mt-2 text-sm font-bold text-slate-800">{comp.name}</h3>
                <p className="mt-1 text-xs leading-5 text-slate-500">{comp.description}</p>

                <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
                  <span className="text-xs font-bold text-slate-600">Minha autoavaliação:</span>
                  <div className="flex items-center gap-1.5">
                    {[1, 2, 3, 4, 5].map((lvl) => (
                      <button
                        key={lvl}
                        type="button"
                        onClick={() => updateCompetencySelfLevel(comp.id, lvl)}
                        className={cx(
                          'flex h-8 w-9 items-center justify-center rounded-lg border text-xs font-bold transition-colors cursor-pointer',
                          comp.studentLevel === lvl
                            ? 'border-sky-700 bg-sky-700 text-white'
                            : 'border-slate-200 bg-white text-slate-600 hover:bg-sky-50',
                        )}
                        data-testid={`btn-self-level-${comp.id}-${lvl}`}
                      >
                        {lvl}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-5">
            <label className="block text-xs font-bold text-slate-700">
              Reflexão pessoal sobre o semestre e práticas de oficina
              <textarea
                rows={3}
                value={reflection}
                onChange={(e) => setReflection(e.target.value)}
                className="mt-2 w-full rounded-xl border border-slate-200 p-3 text-xs font-normal leading-5 text-slate-700 outline-none focus:border-sky-500"
              />
            </label>
          </div>
        </section>

        <section className="space-y-4">
          <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_2px_8px_rgba(34,64,99,.035)]">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="font-[var(--app-font-serif)] text-lg font-bold text-slate-800">
                  Minhas Insígnias & Conquistas
                </h2>
                <p className="mt-1 text-xs text-slate-500">
                  Reconhecimentos por assiduidade, segurança e excelência técnica
                </p>
              </div>
              <span className="rounded-xl bg-amber-50 p-2.5 text-amber-600">
                <Award size={20} />
              </span>
            </div>

            <div className="mt-5 space-y-3">
              {badges.map((badge) => (
                <div
                  key={badge.id}
                  className={cx(
                    'rounded-xl border p-4 transition-all',
                    badge.unlocked
                      ? 'border-sky-100 bg-sky-50/40'
                      : 'border-slate-200 bg-slate-50/60 opacity-75',
                  )}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-2.5">
                      <span
                        className={cx(
                          'flex h-9 w-9 shrink-0 items-center justify-center rounded-xl',
                          badge.unlocked ? 'bg-sky-700 text-white' : 'bg-slate-200 text-slate-500',
                        )}
                      >
                        <Star size={16} />
                      </span>
                      <div>
                        <strong className="block text-xs font-bold text-slate-800">{badge.title}</strong>
                        <span className="text-[11px] font-semibold text-sky-700">
                          {badge.unlocked ? 'Conquista desbloqueada' : `Em progresso (${badge.progress}%)`}
                        </span>
                      </div>
                    </div>
                  </div>
                  <p className="mt-2 text-xs leading-5 text-slate-600">{badge.description}</p>
                  <div className="mt-2.5 h-1.5 overflow-hidden rounded-full bg-slate-200">
                    <div
                      className={cx(
                        'h-full rounded-full',
                        badge.unlocked ? 'bg-emerald-500' : 'bg-sky-600',
                      )}
                      style={{ width: `${badge.progress}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

export function StudentSupportPage() {
  const {
    activeStudent,
    helpRequests,
    submitHelpRequest,
    wallPosts,
    subjects: subjectsQuery,
  } = useAcademicQueries();

  const subjects = subjectsQuery.data ?? [];
  const [subject, setSubject] = useState(subjects[0]?.name || 'Fundamentos de Eletricidade');
  const [bench, setBench] = useState('Bancada 01');
  const [urgency, setUrgency] = useState('Média');
  const [question, setQuestion] = useState('');
  const [sentBanner, setSentBanner] = useState(false);

  const handleSubmit = (event) => {
    event.preventDefault();
    if (!question.trim()) return;
    submitHelpRequest({
      subject,
      bench,
      urgency,
      question: question.trim(),
    });
    setQuestion('');
    setSentBanner(true);
    setTimeout(() => setSentBanner(false), 3000);
  };

  return (
    <main className="animate-rise">
      <PageHeader
        eyebrow="Canal Direto Aluno · Professor"
        title="Mural & Pedir Ajuda"
        description="Envie dúvidas técnicas durante a aula ou oficina e acompanhe os comunicados da sua turma."
      />

      {sentBanner && (
        <div className="mb-5 flex items-center gap-2 rounded-xl border border-emerald-100 bg-emerald-50 px-4 py-3 text-sm font-semibold text-emerald-800">
          <CheckCircle2 size={17} />
          Sua solicitação de ajuda foi enviada para o professor! Acompanhe o retorno abaixo.
        </div>
      )}

      <div className="grid gap-5 xl:grid-cols-[1fr_1fr]">
        <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_2px_8px_rgba(34,64,99,.035)]">
          <h2 className="font-[var(--app-font-serif)] text-lg font-bold text-slate-800">
            Solicitar apoio do professor
          </h2>
          <p className="mt-1 text-xs text-slate-500">
            Informe sua disciplina, bancada e dúvida para que o docente possa orientar você.
          </p>

          <form onSubmit={handleSubmit} className="mt-5 space-y-4">
            <label className="block text-xs font-bold text-slate-700">
              Disciplina / Oficina
              <select
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                className="mt-1.5 h-10 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm font-normal outline-none focus:border-sky-500"
              >
                {subjects.map((s) => (
                  <option key={s.id} value={s.name}>
                    {s.name}
                  </option>
                ))}
              </select>
            </label>

            <div className="grid gap-3 sm:grid-cols-2">
              <label className="block text-xs font-bold text-slate-700">
                Local / Bancada
                <input
                  value={bench}
                  onChange={(e) => setBench(e.target.value)}
                  placeholder="Ex: Bancada 03 · Lab 02"
                  className="mt-1.5 h-10 w-full rounded-xl border border-slate-200 px-3 text-sm font-normal outline-none focus:border-sky-500"
                />
              </label>
              <label className="block text-xs font-bold text-slate-700">
                Prioridade
                <select
                  value={urgency}
                  onChange={(e) => setUrgency(e.target.value)}
                  className="mt-1.5 h-10 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm font-normal outline-none focus:border-sky-500"
                >
                  <option>Baixa</option>
                  <option>Média</option>
                  <option>Alta</option>
                </select>
              </label>
            </div>

            <label className="block text-xs font-bold text-slate-700">
              Descreva sua dúvida ou dificuldade na atividade
              <textarea
                required
                rows={4}
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Explique em qual etapa da atividade prática ou exercício você precisa de ajuda..."
                className="mt-1.5 w-full rounded-xl border border-slate-200 p-3 text-sm font-normal outline-none focus:border-sky-500"
              />
            </label>

            <button
              type="submit"
              className="inline-flex h-10 w-full items-center justify-center gap-2 rounded-xl bg-sky-700 px-4 text-sm font-bold text-white hover:bg-sky-800 cursor-pointer"
              data-testid="button-send-help-request"
            >
              <Send size={15} />
              Enviar solicitação ao professor
            </button>
          </form>
        </section>

        <div className="space-y-5">
          <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_2px_8px_rgba(34,64,99,.035)]">
            <h2 className="font-[var(--app-font-serif)] text-lg font-bold text-slate-800">
              Meus chamados e respostas docentes
            </h2>
            <p className="mt-1 text-xs text-slate-500">
              Histórico de dúvidas enviadas por {activeStudent.name} e colegas da turma
            </p>

            <div className="mt-4 space-y-3">
              {helpRequests.map((req) => (
                <div key={req.id} className="rounded-xl border border-slate-100 bg-slate-50/70 p-3.5">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <strong className="text-xs text-slate-800">{req.subject}</strong>
                      <PriorityBadge priority={req.urgency} />
                      <StatusBadge status={req.status} />
                    </div>
                    <span className="text-[11px] text-slate-400">{req.createdAt}</span>
                  </div>
                  <p className="mt-2 text-xs text-slate-600">"{req.question}"</p>
                  {req.reply && (
                    <div className="mt-2.5 rounded-lg border border-emerald-100 bg-emerald-50 p-2.5 text-xs text-emerald-900">
                      <strong>Resposta do Professor:</strong> {req.reply}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_2px_8px_rgba(34,64,99,.035)]">
            <h2 className="font-[var(--app-font-serif)] text-lg font-bold text-slate-800">
              Mural de avisos da turma
            </h2>
            <div className="mt-4 space-y-3">
              {wallPosts.map((post) => (
                <div key={post.id} className="rounded-xl border border-slate-100 bg-slate-50/70 p-3.5">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="font-bold text-sky-700">
                      {post.tag} · {post.targetClass}
                    </span>
                    <span className="text-slate-400">{post.date}</span>
                  </div>
                  <strong className="mt-1 block text-xs font-bold text-slate-800">{post.title}</strong>
                  <p className="mt-1 text-xs leading-5 text-slate-600">{post.content}</p>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
