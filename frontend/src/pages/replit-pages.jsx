import React, { useMemo, useState } from 'react';
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  BarChart3,
  Bell,
  BookOpen,
  CalendarDays,
  Check,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  ClipboardList,
  Download,
  Eye,
  EyeOff,
  FileText,
  Filter,
  GraduationCap,
  LockKeyhole,
  MoreHorizontal,
  Plus,
  Search,
  Settings,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  TrendingUp,
  UserRound,
  Users,
  X,
} from '../lib/icons';
import { Link, useLocation, useParams } from '../lib/router';
import { useAcademicQueries } from '../context/AcademicContext';
import { INITIAL_PLATFORM_USERS, UsersManagementPanel } from '../components/domain/UsersManagementPanel';
import { UserFormModal } from '../components/domain/UserFormModal';
import {
  cx,
  EmptyState,
  fmt,
  MetricCard,
  Modal,
  OutlineButton,
  PageHeader,
  PriorityBadge,
  RequestState,
  StatusBadge,
} from '../components/ui-primitives';

export function Dashboard() {
  const { dashboard, subjects, alerts } = useAcademicQueries();
  const [period, setPeriod] = useState('1º semestre 2024');
  const blocked = dashboard.isPending || subjects.isPending || alerts.isPending;
  const failed = dashboard.isError || subjects.isError || alerts.isError;
  if (blocked || failed || !dashboard.data || !subjects.data || !alerts.data) {
    return <RequestState loading={blocked} error={failed} />;
  }
  const summary = dashboard.data;
  const distributionColors = ['#214d75', '#3da58d', '#e2ad40', '#c85b57'];
  const distribution = summary.performanceDistribution;
  const totalBandPercentage = distribution.reduce((total, band) => total + band.percentage, 0) || 100;
  let distributionStart = 0;
  const distributionStops = distribution
    .map((band, index) => {
      const end = distributionStart + (band.percentage / totalBandPercentage) * 100;
      const stop = `${distributionColors[index % distributionColors.length]} ${distributionStart}% ${end}%`;
      distributionStart = end;
      return stop;
    })
    .join(', ');

  const monthlyPoints = summary.monthlyAverages
    .map((point, index) => {
      const x = summary.monthlyAverages.length > 1 ? (index / (summary.monthlyAverages.length - 1)) * 700 : 350;
      const y = 195 - ((point.average - 5) / 4) * 175;
      return `${x},${Math.max(10, Math.min(200, y))}`;
    })
    .join(' ');

  const targetPoints = summary.monthlyAverages
    .map((point, index) => {
      const x = summary.monthlyAverages.length > 1 ? (index / (summary.monthlyAverages.length - 1)) * 700 : 350;
      const y = 195 - ((point.target - 5) / 4) * 175;
      return `${x},${Math.max(10, Math.min(200, y))}`;
    })
    .join(' ');

  return (
    <main className="animate-rise">
      <PageHeader
        eyebrow="Visão geral · Professor"
        title="Bom dia, Prof. Mariana."
        description="Acompanhe os sinais das suas turmas que pedem atenção e transforme dados em ação pedagógica."
        actions={
          <>
            <select
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              className="h-10 rounded-xl border border-slate-200 bg-white px-3 text-sm font-medium text-slate-700 outline-none focus:border-sky-500"
              data-testid="select-dashboard-period"
            >
              <option>1º semestre 2024</option>
              <option>2º semestre 2024</option>
              <option>Ano letivo 2024</option>
            </select>
            <OutlineButton
              icon={Download}
              onClick={() => window.alert('Resumo preparado para exportação.')}
              testId="button-export-dashboard"
            >
              Exportar resumo
            </OutlineButton>
          </>
        }
      />
      <div className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Alunos ativos"
          value={String(summary.totalStudents)}
          detail={`${summary.studentsAdded} novos neste período`}
          icon={Users}
          tone="blue"
          trend="up"
        />
        <MetricCard
          label="Média geral"
          value={fmt(summary.overallAverage)}
          detail={`+${fmt(summary.averageChange)} vs. período anterior`}
          icon={TrendingUp}
          tone="green"
          trend="up"
        />
        <MetricCard
          label="Frequência média"
          value={`${summary.averageAttendance.toLocaleString('pt-BR', { maximumFractionDigits: 1 })}%`}
          detail={`+${summary.attendanceChange.toLocaleString('pt-BR', { maximumFractionDigits: 1 })} p.p. no mês`}
          icon={CalendarDays}
          tone="green"
          trend="up"
        />
        <MetricCard
          label="Pedem atenção"
          value={String(summary.attentionStudents)}
          detail={`${summary.criticalStudents} casos críticos`}
          icon={AlertTriangle}
          tone="amber"
          trend="down"
        />
      </div>
      <div className="grid gap-5 xl:grid-cols-[1.45fr_1fr]">
        <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_2px_8px_rgba(34,64,99,.035)]">
          <div className="mb-5 flex items-start justify-between">
            <div>
              <h2 className="font-[var(--app-font-serif)] text-lg font-bold text-slate-800">Evolução da média</h2>
              <p className="mt-1 text-xs text-slate-500">Acompanhe o movimento mensal das turmas</p>
            </div>
            <button
              className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
              data-testid="button-evolution-options"
            >
              <MoreHorizontal size={18} />
            </button>
          </div>
          <div className="relative h-[220px]">
            <div className="absolute inset-0 flex flex-col justify-between text-[10px] text-slate-400">
              <span>9,0</span>
              <span>8,0</span>
              <span>7,0</span>
              <span>6,0</span>
              <span>5,0</span>
            </div>
            <div className="ml-8 h-full border-b border-l border-slate-200 bg-[linear-gradient(to_bottom,transparent_24.5%,#e8edf2_25%,transparent_25.5%,transparent_49.5%,#e8edf2_50%,transparent_50.5%,transparent_74.5%,#e8edf2_75%,transparent_75.5%)]">
              <svg viewBox="0 0 700 210" className="h-full w-full overflow-visible" preserveAspectRatio="none">
                <polyline
                  points={monthlyPoints}
                  fill="none"
                  stroke="#1889a0"
                  strokeWidth="3"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="chart-line"
                />
                <polyline
                  points={targetPoints}
                  fill="none"
                  stroke="#9bb4c9"
                  strokeWidth="2"
                  strokeDasharray="5 5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="chart-line"
                />
              </svg>
            </div>
            <div className="ml-8 flex justify-between pt-2 text-[10px] text-slate-400">
              {summary.monthlyAverages.map((point) => (
                <span key={point.month}>{point.month}</span>
              ))}
            </div>
          </div>
          <div className="mt-4 flex gap-5 text-xs text-slate-500">
            <span className="flex items-center gap-2">
              <i className="h-2 w-2 rounded-full bg-[#1889a0]" />
              Média geral
            </span>
            <span className="flex items-center gap-2">
              <i className="h-2 w-2 rounded-full bg-[#9bb4c9]" />
              Meta institucional · 7,5
            </span>
          </div>
        </section>
        <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_2px_8px_rgba(34,64,99,.035)]">
          <div className="mb-5">
            <h2 className="font-[var(--app-font-serif)] text-lg font-bold text-slate-800">Distribuição de desempenho</h2>
            <p className="mt-1 text-xs text-slate-500">{summary.totalStudents} alunos por faixa de média</p>
          </div>
          <div className="flex items-center gap-6">
            <div
              className="relative flex h-32 w-32 shrink-0 items-center justify-center rounded-full"
              style={{ background: `conic-gradient(${distributionStops})` }}
            >
              <div className="flex h-20 w-20 flex-col items-center justify-center rounded-full bg-white">
                <strong className="font-[var(--app-font-serif)] text-2xl text-slate-800">
                  {fmt(summary.overallAverage)}
                </strong>
                <span className="text-[10px] text-slate-500">média geral</span>
              </div>
            </div>
            <div className="w-full space-y-3 text-xs">
              {distribution.map((band, index) => (
                <div className="flex justify-between" key={band.label}>
                  <span className="flex items-center gap-2 text-slate-600">
                    <i
                      className="h-2 w-2 rounded-full"
                      style={{ backgroundColor: distributionColors[index % distributionColors.length] }}
                    />
                    {band.label}
                  </span>
                  <b className="text-slate-700">
                    {band.count} <span className="font-normal text-slate-400">· {band.percentage}%</span>
                  </b>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>
      <div className="mt-5 grid gap-5 xl:grid-cols-[1fr_1fr]">
        <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_2px_8px_rgba(34,64,99,.035)]">
          <div className="mb-5 flex items-start justify-between">
            <div>
              <h2 className="font-[var(--app-font-serif)] text-lg font-bold text-slate-800">Desempenho por disciplina</h2>
              <p className="mt-1 text-xs text-slate-500">Média e frequência no período selecionado</p>
            </div>
            <Link href="/disciplinas" className="text-xs font-bold text-sky-700 hover:text-sky-900" data-testid="link-view-subjects">
              Ver disciplinas
            </Link>
          </div>
          <div className="space-y-4">
            {subjects.data.slice(0, 4).map((subject) => (
              <div key={subject.id} data-testid={`row-dashboard-subject-${subject.id}`}>
                <div className="mb-1.5 flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-700">{subject.name}</span>
                  <span className="font-bold text-slate-800">{fmt(subject.average)}</span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                  <div
                    className={cx('h-full rounded-full', subject.average < 7 ? 'bg-amber-400' : 'bg-sky-700')}
                    style={{ width: `${subject.average * 10}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </section>
        <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_2px_8px_rgba(34,64,99,.035)]">
          <div className="mb-4 flex items-start justify-between">
            <div>
              <h2 className="font-[var(--app-font-serif)] text-lg font-bold text-slate-800">Atenção necessária</h2>
              <p className="mt-1 text-xs text-slate-500">Sinais recentes que pedem acompanhamento</p>
            </div>
            <Link href="/alertas" className="text-xs font-bold text-sky-700 hover:text-sky-900" data-testid="link-view-alerts">
              Ver todos
            </Link>
          </div>
          <div className="divide-y divide-slate-100">
            {alerts.data.slice(0, 3).map((alert) => (
              <Link
                href={`/alunos/${alert.studentId}`}
                key={alert.id}
                className="flex items-center gap-3 py-3 first:pt-1 last:pb-1 hover:bg-slate-50"
                data-testid={`row-dashboard-alert-${alert.id}`}
              >
                <span
                  className={cx(
                    'rounded-lg p-2',
                    alert.priority === 'Alta' ? 'bg-red-50 text-red-600' : 'bg-amber-50 text-amber-600',
                  )}
                >
                  {alert.priority === 'Alta' ? <AlertCircle size={15} /> : <AlertTriangle size={15} />}
                </span>
                <span className="min-w-0 flex-1">
                  <strong className="block truncate text-xs font-bold text-slate-700">{alert.student}</strong>
                  <small className="block truncate pt-0.5 text-[11px] text-slate-500">{alert.signal}</small>
                </span>
                <ChevronRight size={15} className="text-slate-300" />
              </Link>
            ))}
          </div>
        </section>
      </div>
      <div className="mt-5 rounded-2xl border border-sky-100 bg-[linear-gradient(100deg,#eaf7f8,#f7fbfc)] p-5">
        <div className="flex items-start gap-3">
          <span className="rounded-xl bg-sky-700 p-2 text-white">
            <Sparkles size={17} />
          </span>
          <div>
            <p className="text-sm font-bold text-slate-800">O dado só importa quando apoia uma decisão.</p>
            <p className="mt-1 max-w-3xl text-xs leading-5 text-slate-600">
              Use os sinais acima para priorizar conversas, revisar estratégias de ensino e registrar o acompanhamento de cada estudante.
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}

export function StudentsPage() {
  const { students: studentsQuery, classes: classesQuery, addStudent } = useAcademicQueries();
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('Todos');
  const [classFilter, setClassFilter] = useState('Todas as turmas');
  const [page, setPage] = useState(1);
  const [modalOpen, setModalOpen] = useState(false);
  const [newName, setNewName] = useState('');
  const [newReg, setNewReg] = useState('');
  const [newClass, setNewClass] = useState('Eletrotécnica 2A');
  const [newAvg, setNewAvg] = useState('8.0');
  const [newAtt, setNewAtt] = useState('94');

  const students = studentsQuery.data ?? [];
  const classes = classesQuery.data ?? [];

  const filtered = useMemo(
    () =>
      students.filter(
        (student) =>
          (status === 'Todos' || student.status === status) &&
          (classFilter === 'Todas as turmas' || student.className === classFilter) &&
          `${student.name} ${student.registration} ${student.className}`
            .toLowerCase()
            .includes(search.toLowerCase()),
      ),
    [search, status, classFilter, students],
  );

  if (studentsQuery.isPending || studentsQuery.isError || !studentsQuery.data) {
    return <RequestState loading={studentsQuery.isPending} error={studentsQuery.isError} />;
  }

  const visible = filtered.slice((page - 1) * 6, page * 6);

  const handleCreateStudent = (event) => {
    event.preventDefault();
    if (!newName.trim()) return;
    addStudent({
      name: newName.trim(),
      registration: newReg.trim(),
      className: newClass,
      average: Number(newAvg),
      attendance: Number(newAtt),
    });
    setNewName('');
    setNewReg('');
    setModalOpen(false);
  };

  return (
    <main className="animate-rise">
      <PageHeader
        eyebrow="Acompanhamento"
        title="Alunos"
        description="Consulte o percurso acadêmico e encontre rapidamente quem precisa de acompanhamento."
        actions={
          <OutlineButton
            icon={Users}
            tone="primary"
            onClick={() => setModalOpen(true)}
            testId="button-new-student"
          >
            Novo aluno
          </OutlineButton>
        }
      />
      <div className="mb-5 flex flex-col gap-3 rounded-2xl border border-slate-200/80 bg-white p-3 shadow-[0_2px_8px_rgba(34,64,99,.035)] md:flex-row">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-3 text-slate-400" />
          <input
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            placeholder="Buscar por nome, matrícula ou turma"
            className="h-10 w-full rounded-xl border border-slate-200 bg-slate-50 pl-9 pr-3 text-sm text-slate-700 outline-none focus:border-sky-500 focus:bg-white"
            data-testid="input-search-students"
          />
        </div>
        <div className="flex flex-wrap gap-2">
          <select
            value={classFilter}
            onChange={(e) => {
              setClassFilter(e.target.value);
              setPage(1);
            }}
            className="h-10 rounded-xl border border-slate-200 bg-white px-3 text-sm text-slate-600 outline-none focus:border-sky-500"
          >
            <option>Todas as turmas</option>
            {classes.map((c) => (
              <option key={c.id} value={c.name}>
                {c.name}
              </option>
            ))}
          </select>
          <select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(1);
            }}
            className="h-10 rounded-xl border border-slate-200 bg-white px-3 text-sm text-slate-600 outline-none focus:border-sky-500"
            data-testid="select-student-status"
          >
            <option>Todos</option>
            <option>Regular</option>
            <option>Atenção</option>
            <option>Crítico</option>
          </select>
          <button
            onClick={() => {
              setSearch('');
              setStatus('Todos');
              setClassFilter('Todas as turmas');
              setPage(1);
            }}
            className="inline-flex h-10 items-center gap-2 rounded-xl border border-slate-200 px-3 text-sm font-semibold text-slate-600 hover:bg-slate-50"
            data-testid="button-student-filter"
          >
            <Filter size={15} />
            Limpar
          </button>
        </div>
      </div>

      <div className="overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-[0_2px_8px_rgba(34,64,99,.035)]">
        <div className="hidden overflow-x-auto md:block">
          <table className="w-full min-w-[800px] text-left">
            <thead className="border-b border-slate-100 bg-slate-50/70">
              <tr>
                {['Aluno', 'Turma', 'Média', 'Frequência', 'Situação', 'Atualizado', ''].map((head) => (
                  <th key={head} className="px-5 py-3 text-[10px] font-bold uppercase tracking-[.09em] text-slate-500">
                    {head}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {visible.map((student) => (
                <tr key={student.id} className="group hover:bg-slate-50/70" data-testid={`row-student-${student.id}`}>
                  <td className="px-5 py-4">
                    <Link
                      href={`/alunos/${student.id}`}
                      className="flex items-center gap-3"
                      data-testid={`link-student-${student.id}`}
                    >
                      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-sky-50 text-xs font-bold text-sky-800">
                        {student.name
                          .split(' ')
                          .map((n) => n[0])
                          .slice(0, 2)
                          .join('')}
                      </span>
                      <span>
                        <strong className="block text-sm font-bold text-slate-700">{student.name}</strong>
                        <small className="text-xs text-slate-400">#{student.registration}</small>
                      </span>
                    </Link>
                  </td>
                  <td className="px-5 py-4 text-xs text-slate-600">{student.className}</td>
                  <td className="px-5 py-4 text-sm font-bold text-slate-700">{fmt(student.average)}</td>
                  <td className="px-5 py-4 text-sm font-semibold text-slate-700">{student.attendance}%</td>
                  <td className="px-5 py-4">
                    <StatusBadge status={student.status} />
                  </td>
                  <td className="px-5 py-4 text-xs text-slate-400">{student.updatedAt}</td>
                  <td className="px-5 py-4 text-right">
                    <Link
                      href={`/alunos/${student.id}`}
                      className="inline-flex rounded-lg p-2 text-slate-400 hover:bg-sky-50 hover:text-sky-700"
                      data-testid={`button-view-student-${student.id}`}
                    >
                      <ChevronRight size={17} />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="divide-y divide-slate-100 md:hidden">
          {visible.map((student) => (
            <Link
              href={`/alunos/${student.id}`}
              key={student.id}
              className="flex items-center gap-3 p-4"
              data-testid={`card-student-${student.id}`}
            >
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-sky-50 text-xs font-bold text-sky-800">
                {student.name
                  .split(' ')
                  .map((n) => n[0])
                  .slice(0, 2)
                  .join('')}
              </span>
              <span className="min-w-0 flex-1">
                <strong className="block truncate text-sm text-slate-700">{student.name}</strong>
                <small className="text-xs text-slate-400">
                  {student.className} · Média {fmt(student.average)}
                </small>
              </span>
              <StatusBadge status={student.status} />
              <ChevronRight size={16} className="text-slate-300" />
            </Link>
          ))}
        </div>

        {visible.length === 0 && (
          <EmptyState
            title="Nenhum aluno encontrado"
            detail="Tente buscar por outro nome, matrícula ou alterar o filtro de situação."
          />
        )}

        <div className="flex items-center justify-between border-t border-slate-100 px-5 py-3">
          <span className="text-xs text-slate-500">{filtered.length} alunos encontrados</span>
          <div className="flex items-center gap-1">
            <button
              disabled={page === 1}
              onClick={() => setPage((current) => current - 1)}
              className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 disabled:opacity-30"
              data-testid="button-student-previous"
            >
              <ChevronLeft size={16} />
            </button>
            <span className="px-2 text-xs font-semibold text-slate-600">Página {page}</span>
            <button
              disabled={page * 6 >= filtered.length}
              onClick={() => setPage((current) => current + 1)}
              className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 disabled:opacity-30"
              data-testid="button-student-next"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      </div>

      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title="Cadastrar e matricular novo aluno"
        subtitle="Vincule o estudante a uma turma ativa para iniciar o monitoramento acadêmico."
      >
        <form onSubmit={handleCreateStudent} className="space-y-4">
          <label className="block text-xs font-bold text-slate-700">
            Nome completo do estudante
            <input
              required
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Ex: Lucas Fernandes de Oliveira"
              className="mt-1.5 h-10 w-full rounded-xl border border-slate-200 px-3 text-sm font-normal outline-none focus:border-sky-500"
            />
          </label>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="block text-xs font-bold text-slate-700">
              Matrícula (RA)
              <input
                value={newReg}
                onChange={(e) => setNewReg(e.target.value)}
                placeholder="Ex: 2024.0412"
                className="mt-1.5 h-10 w-full rounded-xl border border-slate-200 px-3 text-sm font-normal outline-none focus:border-sky-500"
              />
            </label>
            <label className="block text-xs font-bold text-slate-700">
              Turma
              <select
                value={newClass}
                onChange={(e) => setNewClass(e.target.value)}
                className="mt-1.5 h-10 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm font-normal outline-none focus:border-sky-500"
              >
                {classes.map((c) => (
                  <option key={c.id} value={c.name}>
                    {c.name}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="block text-xs font-bold text-slate-700">
              Média inicial (0 a 10)
              <input
                type="number"
                step="0.1"
                min="0"
                max="10"
                value={newAvg}
                onChange={(e) => setNewAvg(e.target.value)}
                className="mt-1.5 h-10 w-full rounded-xl border border-slate-200 px-3 text-sm font-normal outline-none focus:border-sky-500"
              />
            </label>
            <label className="block text-xs font-bold text-slate-700">
              Frequência inicial (%)
              <input
                type="number"
                min="0"
                max="100"
                value={newAtt}
                onChange={(e) => setNewAtt(e.target.value)}
                className="mt-1.5 h-10 w-full rounded-xl border border-slate-200 px-3 text-sm font-normal outline-none focus:border-sky-500"
              />
            </label>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <OutlineButton onClick={() => setModalOpen(false)}>Cancelar</OutlineButton>
            <OutlineButton type="submit" tone="primary">
              Salvar matrícula
            </OutlineButton>
          </div>
        </form>
      </Modal>
    </main>
  );
}

export function StudentDetail() {
  const { id } = useParams();
  const { getStudentProfileById, addStudentHistory } = useAcademicQueries();
  const [noteModalOpen, setNoteModalOpen] = useState(false);
  const [noteTitle, setNoteTitle] = useState('');
  const [noteDetail, setNoteDetail] = useState('');

  const profile = getStudentProfileById(id || 's-01');
  if (!profile) {
    return <RequestState loading={false} error={true} />;
  }

  const { student, subjects: profileSubjects, history } = profile;

  const handleSaveNote = (event) => {
    event.preventDefault();
    if (!noteTitle.trim() || !noteDetail.trim()) return;
    addStudentHistory(student.id, {
      title: noteTitle.trim(),
      detail: noteDetail.trim(),
    });
    setNoteTitle('');
    setNoteDetail('');
    setNoteModalOpen(false);
  };

  return (
    <main className="animate-rise">
      <Link
        href="/alunos"
        className="mb-5 inline-flex items-center gap-1 text-xs font-semibold text-slate-500 hover:text-sky-700"
        data-testid="link-back-students"
      >
        <ChevronLeft size={15} />
        Voltar para alunos
      </Link>
      <div className="mb-6 rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_2px_8px_rgba(34,64,99,.035)] md:p-6">
        <div className="flex flex-col justify-between gap-5 md:flex-row md:items-center">
          <div className="flex items-center gap-4">
            <span className="flex h-16 w-16 items-center justify-center rounded-2xl bg-sky-50 font-[var(--app-font-serif)] text-xl font-bold text-sky-800">
              {student.name
                .split(' ')
                .map((n) => n[0])
                .slice(0, 2)
                .join('')}
            </span>
            <div>
              <div className="mb-1 flex flex-wrap items-center gap-2">
                <h1 className="font-[var(--app-font-serif)] text-2xl font-bold tracking-tight text-slate-800">
                  {student.name}
                </h1>
                <StatusBadge status={student.status} />
              </div>
              <p className="text-sm text-slate-500">
                {student.course} · {student.className}
              </p>
              <p className="mt-1 text-xs text-slate-400">
                Matrícula {student.registration} · Última atualização {student.updatedAt}
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <OutlineButton
              icon={FileText}
              onClick={() => setNoteModalOpen(true)}
              testId="button-add-pedagogical-note"
            >
              Registrar acompanhamento
            </OutlineButton>
            <button
              className="rounded-xl border border-slate-200 p-2.5 text-slate-500 hover:bg-slate-50"
              data-testid="button-student-more"
            >
              <MoreHorizontal size={17} />
            </button>
          </div>
        </div>
      </div>

      <div className="mb-5 grid gap-4 sm:grid-cols-3">
        <MetricCard
          label="Média atual"
          value={fmt(student.average)}
          detail="+0,4 no último ciclo"
          icon={TrendingUp}
          tone="green"
          trend="up"
        />
        <MetricCard
          label="Frequência"
          value={`${student.attendance}%`}
          detail={student.attendance >= 75 ? 'Acima do limite de 75%' : 'Abaixo do limite regimental de 75%'}
          icon={CalendarDays}
          tone={student.attendance >= 75 ? 'blue' : 'red'}
          trend={student.attendance >= 75 ? 'up' : 'down'}
        />
        <MetricCard
          label="Avaliações"
          value="14 / 16"
          detail="2 atividades pendentes"
          icon={ClipboardList}
          tone="amber"
        />
      </div>

      <div className="grid gap-5 xl:grid-cols-[1.15fr_.85fr]">
        <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_2px_8px_rgba(34,64,99,.035)]">
          <h2 className="font-[var(--app-font-serif)] text-lg font-bold text-slate-800">Evolução de desempenho</h2>
          <p className="mt-1 text-xs text-slate-500">Média nas últimas avaliações</p>
          <div className="mt-5 h-52">
            <svg viewBox="0 0 700 190" className="h-full w-full overflow-visible" preserveAspectRatio="none">
              <path
                d="M0,145 C90,138 100,126 160,130 S235,110 295,117 S380,84 440,96 S525,72 575,78 S650,46 700,50"
                fill="none"
                stroke="#214d75"
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
            <span>Projeto</span>
            <span>Atual</span>
          </div>
        </section>

        <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_2px_8px_rgba(34,64,99,.035)]">
          <h2 className="font-[var(--app-font-serif)] text-lg font-bold text-slate-800">Desempenho por disciplina</h2>
          <p className="mt-1 text-xs text-slate-500">Visão do ciclo atual</p>
          <div className="mt-5 space-y-4">
            {profileSubjects.slice(0, 4).map((subject) => (
              <div key={subject.id} className="flex items-center gap-3">
                <span className="w-28 truncate text-xs font-semibold text-slate-600">
                  {subject.name.split(' ').slice(0, 2).join(' ')}
                </span>
                <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
                  <div
                    className={cx(
                      'h-full rounded-full',
                      subject.status === 'Regular'
                        ? 'bg-sky-700'
                        : subject.status === 'Atenção'
                          ? 'bg-amber-400'
                          : 'bg-red-500',
                    )}
                    style={{ width: `${(subject.average / 10) * 100}%` }}
                  />
                </div>
                <span className="w-7 text-right text-xs font-bold text-slate-700">{fmt(subject.average)}</span>
              </div>
            ))}
          </div>
        </section>
      </div>

      <section className="mt-5 rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_2px_8px_rgba(34,64,99,.035)]">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="font-[var(--app-font-serif)] text-lg font-bold text-slate-800">Histórico pedagógico</h2>
            <p className="mt-1 text-xs text-slate-500">Registros de acompanhamento e decisões tomadas</p>
          </div>
          <button
            onClick={() => setNoteModalOpen(true)}
            className="text-xs font-bold text-sky-700 hover:text-sky-900"
            data-testid="button-new-history"
          >
            + Novo registro
          </button>
        </div>
        <div className="space-y-5 border-l border-slate-200 pl-5">
          {history.map((event) => (
            <div className="relative" key={`${event.date}-${event.title}`}>
              <span className="absolute -left-[25px] top-0.5 h-3 w-3 rounded-full border-2 border-white bg-sky-600 ring-1 ring-sky-200" />
              <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                {event.date} · {event.author}
              </p>
              <p className="mt-1 text-sm font-semibold text-slate-700">{event.title}</p>
              <p className="mt-1 text-xs leading-5 text-slate-500">{event.detail}</p>
            </div>
          ))}
        </div>
      </section>

      <Modal
        open={noteModalOpen}
        onClose={() => setNoteModalOpen(false)}
        title={`Registrar acompanhamento · ${student.name}`}
        subtitle="Adicione uma observação pedagógica, feedback de oficina ou plano de recuperação."
      >
        <form onSubmit={handleSaveNote} className="space-y-4">
          <label className="block text-xs font-bold text-slate-700">
            Título do registro
            <input
              required
              value={noteTitle}
              onChange={(e) => setNoteTitle(e.target.value)}
              placeholder="Ex: Orientação individual em laboratório"
              className="mt-1.5 h-10 w-full rounded-xl border border-slate-200 px-3 text-sm font-normal outline-none focus:border-sky-500"
            />
          </label>
          <label className="block text-xs font-bold text-slate-700">
            Detalhamento pedagógico
            <textarea
              required
              rows={4}
              value={noteDetail}
              onChange={(e) => setNoteDetail(e.target.value)}
              placeholder="Descreva a evolução observada, dificuldades identificadas e próximos passos..."
              className="mt-1.5 w-full rounded-xl border border-slate-200 p-3 text-sm font-normal outline-none focus:border-sky-500"
            />
          </label>
          <div className="flex justify-end gap-2 pt-2">
            <OutlineButton onClick={() => setNoteModalOpen(false)}>Cancelar</OutlineButton>
            <OutlineButton type="submit" tone="primary">
              Salvar no histórico
            </OutlineButton>
          </div>
        </form>
      </Modal>
    </main>
  );
}

export function ClassesPage() {
  const { classes: classesQuery, addClassGroup } = useAcademicQueries();
  const [selected, setSelected] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [className, setClassName] = useState('');
  const [courseName, setCourseName] = useState('Técnico em Eletrotécnica');
  const [studentsCount, setStudentsCount] = useState('30');

  if (classesQuery.isPending || classesQuery.isError || !classesQuery.data) {
    return <RequestState loading={classesQuery.isPending} error={classesQuery.isError} />;
  }
  const classes = classesQuery.data;

  const handleCreateClass = (event) => {
    event.preventDefault();
    if (!className.trim()) return;
    addClassGroup({
      name: className.trim(),
      course: courseName,
      students: Number(studentsCount),
    });
    setClassName('');
    setModalOpen(false);
  };

  return (
    <main className="animate-rise">
      <PageHeader
        eyebrow="Acompanhamento"
        title="Turmas"
        description="Uma leitura rápida da saúde acadêmica de cada turma e seus principais sinais."
        actions={
          <>
            <OutlineButton
              icon={Plus}
              tone="primary"
              onClick={() => setModalOpen(true)}
              testId="button-new-class"
            >
              Nova turma
            </OutlineButton>
            <OutlineButton
              icon={Download}
              onClick={() => window.alert('Visão de turmas exportada.')}
              testId="button-export-classes"
            >
              Exportar visão
            </OutlineButton>
          </>
        }
      />
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {classes.map((item) => (
          <div
            key={item.id}
            role="button"
            tabIndex={0}
            onClick={() => setSelected(selected === item.id ? null : item.id)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' || event.key === ' ') setSelected(selected === item.id ? null : item.id);
            }}
            className={cx(
              'group rounded-2xl border bg-white p-5 text-left shadow-[0_2px_8px_rgba(34,64,99,.035)] transition-all hover:-translate-y-0.5 hover:border-sky-200 cursor-pointer',
              selected === item.id ? 'border-sky-400 ring-2 ring-sky-100' : 'border-slate-200/80',
            )}
            data-testid={`card-class-${item.id}`}
          >
            <div className="flex items-start justify-between">
              <div>
                <span className="text-[11px] font-bold uppercase tracking-wider text-sky-700">
                  {item.course.replace('Técnico em ', '')}
                </span>
                <h2 className="mt-1 font-[var(--app-font-serif)] text-lg font-bold text-slate-800">{item.name}</h2>
              </div>
              <StatusBadge status={item.status} />
            </div>
            <div className="mt-6 grid grid-cols-3 gap-3 border-t border-slate-100 pt-4">
              <div>
                <p className="text-[10px] uppercase tracking-wider text-slate-400">Alunos</p>
                <b className="mt-1 block text-lg text-slate-700">{item.students}</b>
              </div>
              <div>
                <p className="text-[10px] uppercase tracking-wider text-slate-400">Média</p>
                <b className="mt-1 block text-lg text-slate-700">{fmt(item.average)}</b>
              </div>
              <div>
                <p className="text-[10px] uppercase tracking-wider text-slate-400">Atenção</p>
                <b className={cx('mt-1 block text-lg', item.attentionCount > 5 ? 'text-amber-600' : 'text-slate-700')}>
                  {item.attentionCount}
                </b>
              </div>
            </div>
            {selected === item.id && (
              <div className="mt-4 rounded-xl bg-slate-50 p-3 text-xs text-slate-600">
                <div className="mb-2 flex justify-between">
                  <span>Frequência média</span>
                  <strong>{item.attendance}%</strong>
                </div>
                <div className="h-1.5 rounded-full bg-slate-200">
                  <div className="h-full rounded-full bg-sky-700" style={{ width: `${item.attendance}%` }} />
                </div>
                <div className="mt-3 flex items-center justify-between">
                  <Link
                    href="/alunos"
                    onClick={(event) => event.stopPropagation()}
                    className="inline-flex items-center gap-1 font-bold text-sky-700"
                    data-testid={`link-class-students-${item.id}`}
                  >
                    Ver alunos <ChevronRight size={13} />
                  </Link>
                  <Link
                    href="/oficina"
                    onClick={(event) => event.stopPropagation()}
                    className="inline-flex items-center gap-1 font-bold text-emerald-700"
                  >
                    Abrir chamada/oficina <ChevronRight size={13} />
                  </Link>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title="Criar nova turma"
        subtitle="Cadastre uma nova turma e período letivo para monitoramento."
      >
        <form onSubmit={handleCreateClass} className="space-y-4">
          <label className="block text-xs font-bold text-slate-700">
            Identificação da turma
            <input
              required
              value={className}
              onChange={(e) => setClassName(e.target.value)}
              placeholder="Ex: Automação 2B"
              className="mt-1.5 h-10 w-full rounded-xl border border-slate-200 px-3 text-sm font-normal outline-none focus:border-sky-500"
            />
          </label>
          <label className="block text-xs font-bold text-slate-700">
            Curso Técnico SENAI
            <input
              required
              value={courseName}
              onChange={(e) => setCourseName(e.target.value)}
              placeholder="Ex: Técnico em Automação Industrial"
              className="mt-1.5 h-10 w-full rounded-xl border border-slate-200 px-3 text-sm font-normal outline-none focus:border-sky-500"
            />
          </label>
          <label className="block text-xs font-bold text-slate-700">
            Quantidade de estudantes matriculados
            <input
              type="number"
              min="1"
              max="60"
              value={studentsCount}
              onChange={(e) => setStudentsCount(e.target.value)}
              className="mt-1.5 h-10 w-full rounded-xl border border-slate-200 px-3 text-sm font-normal outline-none focus:border-sky-500"
            />
          </label>
          <div className="flex justify-end gap-2 pt-2">
            <OutlineButton onClick={() => setModalOpen(false)}>Cancelar</OutlineButton>
            <OutlineButton type="submit" tone="primary">
              Criar turma
            </OutlineButton>
          </div>
        </form>
      </Modal>
    </main>
  );
}

export function SubjectsPage() {
  const { subjects: subjectsQuery, addSubject } = useAcademicQueries();
  const [modalOpen, setModalOpen] = useState(false);
  const [subName, setSubName] = useState('');
  const [subTeacher, setSubTeacher] = useState('Prof. Mariana Costa');
  const [subClasses, setSubClasses] = useState('Eletrotécnica 2A');

  if (subjectsQuery.isPending || subjectsQuery.isError || !subjectsQuery.data) {
    return <RequestState loading={subjectsQuery.isPending} error={subjectsQuery.isError} />;
  }
  const subjects = subjectsQuery.data;

  const handleCreateSubject = (event) => {
    event.preventDefault();
    if (!subName.trim()) return;
    addSubject({
      name: subName.trim(),
      teacher: subTeacher.trim(),
      classes: subClasses.trim(),
    });
    setSubName('');
    setModalOpen(false);
  };

  return (
    <main className="animate-rise">
      <PageHeader
        eyebrow="Acompanhamento"
        title="Disciplinas"
        description="Compare médias, frequência e a concentração de estudantes que precisam de apoio."
        actions={
          <>
            <OutlineButton
              icon={Plus}
              tone="primary"
              onClick={() => setModalOpen(true)}
              testId="button-new-subject"
            >
              Nova disciplina
            </OutlineButton>
            <OutlineButton
              icon={Download}
              onClick={() => window.alert('Relatório de disciplinas exportado.')}
              testId="button-export-subjects"
            >
              Exportar dados
            </OutlineButton>
          </>
        }
      />
      <div className="overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-[0_2px_8px_rgba(34,64,99,.035)]">
        <div className="hidden overflow-x-auto md:block">
          <table className="w-full min-w-[780px] text-left">
            <thead className="border-b border-slate-100 bg-slate-50/70">
              <tr>
                {['Disciplina', 'Professor responsável', 'Turmas', 'Média', 'Frequência', 'Atenção', ''].map((head) => (
                  <th key={head} className="px-5 py-3 text-[10px] font-bold uppercase tracking-[.09em] text-slate-500">
                    {head}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {subjects.map((subject) => (
                <tr key={subject.id} className="hover:bg-slate-50/60" data-testid={`row-subject-${subject.id}`}>
                  <td className="px-5 py-4">
                    <div className="flex items-center gap-3">
                      <span className="rounded-lg bg-sky-50 p-2 text-sky-700">
                        <BookOpen size={15} />
                      </span>
                      <strong className="text-sm text-slate-700">{subject.name}</strong>
                    </div>
                  </td>
                  <td className="px-5 py-4 text-xs text-slate-600">{subject.teacher}</td>
                  <td className="px-5 py-4 text-xs text-slate-500">{subject.classes}</td>
                  <td className="px-5 py-4 text-sm font-bold text-slate-700">{fmt(subject.average)}</td>
                  <td className="px-5 py-4 text-sm font-semibold text-slate-700">{subject.attendance}%</td>
                  <td className="px-5 py-4">
                    <span className={cx('text-sm font-bold', subject.attentionCount > 7 ? 'text-amber-600' : 'text-slate-700')}>
                      {subject.attentionCount}
                    </span>
                  </td>
                  <td className="px-5 py-4 text-right">
                    <button
                      className="rounded-lg p-2 text-slate-400 hover:bg-slate-100"
                      data-testid={`button-subject-more-${subject.id}`}
                    >
                      <MoreHorizontal size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="divide-y divide-slate-100 md:hidden">
          {subjects.map((subject) => (
            <div key={subject.id} className="p-4">
              <div className="flex justify-between gap-3">
                <div>
                  <strong className="text-sm text-slate-700">{subject.name}</strong>
                  <p className="mt-1 text-xs text-slate-500">{subject.teacher}</p>
                </div>
                <span className="text-lg font-bold text-slate-700">{fmt(subject.average)}</span>
              </div>
              <div className="mt-3 flex gap-4 text-xs text-slate-500">
                <span>
                  Freq. <b className="text-slate-700">{subject.attendance}%</b>
                </span>
                <span>
                  Atenção <b className="text-amber-600">{subject.attentionCount}</b>
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title="Cadastrar disciplina e atribuir docente"
        subtitle="Vincule a unidade curricular às turmas e ao professor responsável."
      >
        <form onSubmit={handleCreateSubject} className="space-y-4">
          <label className="block text-xs font-bold text-slate-700">
            Nome da disciplina / unidade curricular
            <input
              required
              value={subName}
              onChange={(e) => setSubName(e.target.value)}
              placeholder="Ex: Controladores Lógicos Programáveis (CLP)"
              className="mt-1.5 h-10 w-full rounded-xl border border-slate-200 px-3 text-sm font-normal outline-none focus:border-sky-500"
            />
          </label>
          <label className="block text-xs font-bold text-slate-700">
            Professor responsável
            <input
              required
              value={subTeacher}
              onChange={(e) => setSubTeacher(e.target.value)}
              className="mt-1.5 h-10 w-full rounded-xl border border-slate-200 px-3 text-sm font-normal outline-none focus:border-sky-500"
            />
          </label>
          <label className="block text-xs font-bold text-slate-700">
            Turmas vinculadas
            <input
              required
              value={subClasses}
              onChange={(e) => setSubClasses(e.target.value)}
              placeholder="Ex: Eletrotécnica 2A · Mecânica 1B"
              className="mt-1.5 h-10 w-full rounded-xl border border-slate-200 px-3 text-sm font-normal outline-none focus:border-sky-500"
            />
          </label>
          <div className="flex justify-end gap-2 pt-2">
            <OutlineButton onClick={() => setModalOpen(false)}>Cancelar</OutlineButton>
            <OutlineButton type="submit" tone="primary">
              Salvar disciplina
            </OutlineButton>
          </div>
        </form>
      </Modal>
    </main>
  );
}

export function AnalysisPage({ kind = 'desempenho' }) {
  const { dashboard: dashboardQuery, students: studentsQuery, subjects: subjectsQuery } = useAcademicQueries();
  const attendance = kind === 'frequencia';
  const blocked = dashboardQuery.isPending || studentsQuery.isPending || subjectsQuery.isPending;
  const failed = dashboardQuery.isError || studentsQuery.isError || subjectsQuery.isError;
  if (blocked || failed || !dashboardQuery.data || !studentsQuery.data || !subjectsQuery.data) {
    return <RequestState loading={blocked} error={failed} />;
  }

  const summary = dashboardQuery.data;
  const students = studentsQuery.data;
  const subjects = subjectsQuery.data;
  const trend = attendance ? summary.monthlyAttendance : summary.monthlyAverages;
  const distribution = attendance ? summary.attendanceDistribution : summary.performanceDistribution;
  const attentionStudents = students.filter((student) => (attendance ? student.attendance < 75 : student.average < 6));
  const studentNeedingSupport = [...students].sort((a, b) =>
    attendance ? a.attendance - b.attendance : a.average - b.average,
  )[0];
  const subjectNeedingSupport = [...subjects].sort((a, b) => a.average - b.average)[0];
  const minValue = attendance ? 70 : 4;
  const maxValue = attendance ? 100 : 10;
  const toPoints = (key) =>
    trend
      .map((point, index) => {
        const x = trend.length > 1 ? (index / (trend.length - 1)) * 700 : 350;
        const y = 195 - ((point[key] - minValue) / (maxValue - minValue)) * 175;
        return `${x},${Math.max(10, Math.min(200, y))}`;
      })
      .join(' ');
  const bandColors = ['bg-emerald-500', 'bg-sky-600', 'bg-amber-400', 'bg-red-500'];
  const trendValue = attendance ? summary.averageAttendance : summary.overallAverage;

  return (
    <main className="animate-rise">
      <PageHeader
        eyebrow="Análise acadêmica"
        title={attendance ? 'Frequência' : 'Desempenho'}
        description={
          attendance
            ? 'Identifique ausências recorrentes e aja antes que elas comprometam a aprendizagem.'
            : 'Cruze resultados, evolução e distribuição para orientar as próximas ações pedagógicas.'
        }
        actions={
          <OutlineButton
            icon={Download}
            onClick={() => window.alert('Análise preparada para exportação.')}
            testId="button-export-analysis"
          >
            Exportar análise
          </OutlineButton>
        }
      />
      <div className="mb-5 grid gap-4 sm:grid-cols-3">
        <MetricCard
          label={attendance ? 'Frequência média' : 'Média geral'}
          value={attendance ? `${fmt(trendValue)}%` : fmt(trendValue)}
          detail={
            attendance
              ? `+${summary.attendanceChange.toLocaleString('pt-BR', { maximumFractionDigits: 1 })} p.p. no mês`
              : `+${fmt(summary.averageChange)} vs. período anterior`
          }
          icon={attendance ? CalendarDays : TrendingUp}
          tone="green"
          trend="up"
        />
        <MetricCard
          label={attendance ? 'Abaixo de 75%' : 'Abaixo de 6,0'}
          value={String(attentionStudents.length)}
          detail="estudantes identificados"
          icon={AlertTriangle}
          tone="amber"
        />
        <MetricCard
          label="Maior atenção"
          value={attendance ? studentNeedingSupport?.name ?? '—' : subjectNeedingSupport?.name ?? '—'}
          detail={
            attendance
              ? `${studentNeedingSupport?.attendance ?? '—'}% de frequência`
              : `Média ${fmt(subjectNeedingSupport?.average ?? 0)}`
          }
          icon={Activity}
          tone="blue"
        />
      </div>
      <div className="grid gap-5 xl:grid-cols-[1.35fr_.65fr]">
        <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_2px_8px_rgba(34,64,99,.035)]">
          <div className="mb-5">
            <h2 className="font-[var(--app-font-serif)] text-lg font-bold text-slate-800">
              {attendance ? 'Evolução da frequência' : 'Evolução das médias'}
            </h2>
            <p className="mt-1 text-xs text-slate-500">Comparativo mensal do ano letivo</p>
          </div>
          <div className="surface-grid h-[260px] rounded-xl p-4">
            <svg viewBox="0 0 700 220" className="h-full w-full overflow-visible" preserveAspectRatio="none">
              <polyline
                points={toPoints('average')}
                fill="none"
                stroke={attendance ? '#3da58d' : '#214d75'}
                strokeWidth="3"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="chart-line"
              />
              <polyline
                points={toPoints('target')}
                fill="none"
                stroke="#b9cbd8"
                strokeWidth="2"
                strokeDasharray="5 5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>
          <div className="mt-3 flex justify-between text-[10px] text-slate-400">
            {trend.map((point) => (
              <span key={point.month}>{point.month}</span>
            ))}
          </div>
        </section>
        <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_2px_8px_rgba(34,64,99,.035)]">
          <h2 className="font-[var(--app-font-serif)] text-lg font-bold text-slate-800">
            {attendance ? 'Faixas de frequência' : 'Distribuição de notas'}
          </h2>
          <p className="mt-1 text-xs text-slate-500">Visão consolidada de {summary.totalStudents} estudantes</p>
          <div className="mt-7 space-y-5">
            {distribution.map((band, index) => (
              <div key={band.label}>
                <div className="mb-1.5 flex justify-between gap-2 text-xs">
                  <span className="text-slate-600">{band.label}</span>
                  <b className="text-slate-700">
                    {band.count} · {band.percentage}%
                  </b>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                  <div
                    className={cx('h-full rounded-full', bandColors[index % bandColors.length])}
                    style={{ width: `${band.percentage}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
      <section className="mt-5 rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_2px_8px_rgba(34,64,99,.035)]">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="font-[var(--app-font-serif)] text-lg font-bold text-slate-800">Estudantes que pedem atenção</h2>
            <p className="mt-1 text-xs text-slate-500">
              {attendance ? 'Abaixo do limite de frequência configurado (75%)' : 'Menores médias no período atual'}
            </p>
          </div>
          <Link href="/alertas" className="text-xs font-bold text-sky-700" data-testid="link-analysis-alerts">
            Abrir alertas
          </Link>
        </div>
        <div className="grid gap-3 md:grid-cols-3">
          {attentionStudents.slice(0, 3).map((student) => (
            <Link
              href={`/alunos/${student.id}`}
              key={student.id}
              className="rounded-xl border border-slate-100 bg-slate-50/70 p-3 hover:border-sky-200 hover:bg-sky-50/50"
              data-testid={`card-analysis-student-${student.id}`}
            >
              <div className="flex items-center justify-between">
                <strong className="text-xs text-slate-700">{student.name}</strong>
                <ChevronRight size={14} className="text-slate-400" />
              </div>
              <p className="mt-2 text-[11px] text-slate-500">{student.className}</p>
              <p className="mt-2 text-sm font-bold text-slate-800">
                {attendance ? `${student.attendance}% de frequência` : `Média ${fmt(student.average)}`}
              </p>
            </Link>
          ))}
          {attentionStudents.length === 0 && (
            <EmptyState
              title="Nenhum estudante nesta faixa"
              detail="Os dados atuais não têm estudantes abaixo do limite configurado."
            />
          )}
        </div>
      </section>
    </main>
  );
}

export function AlertsPage() {
  const { alerts: alertsQuery, toggleAlertFollow } = useAcademicQueries();
  const alerts = alertsQuery.data ?? [];
  const [filter, setFilter] = useState('Todos');
  const filtered = alerts.filter((alert) => filter === 'Todos' || alert.priority === filter);

  if (alertsQuery.isPending || alertsQuery.isError || !alertsQuery.data) {
    return <RequestState loading={alertsQuery.isPending} error={alertsQuery.isError} />;
  }

  return (
    <main className="animate-rise">
      <PageHeader
        eyebrow="Gestão Pedagógica"
        title="Central de alertas"
        description="Priorize os sinais acadêmicos e registre o que já está em acompanhamento."
        actions={
          <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs text-slate-500">
            <span className="h-2 w-2 rounded-full bg-red-500" />
            {alerts.filter((alert) => !alert.followed).length} sem acompanhamento
          </div>
        }
      />
      <div className="mb-5 flex items-center gap-2 overflow-x-auto">
        {['Todos', 'Alta', 'Média', 'Baixa'].map((item) => (
          <button
            onClick={() => setFilter(item)}
            key={item}
            className={cx(
              'rounded-xl px-3.5 py-2 text-xs font-bold transition-colors cursor-pointer',
              filter === item ? 'bg-sky-700 text-white' : 'bg-white text-slate-500 hover:bg-slate-100',
            )}
            data-testid={`button-alert-filter-${item.toLowerCase()}`}
          >
            {item}
            {item !== 'Todos' && (
              <span className="ml-1.5 opacity-70">
                · {alerts.filter((alert) => alert.priority === item).length}
              </span>
            )}
          </button>
        ))}
      </div>
      <div className="space-y-3">
        {filtered.map((alert) => (
          <div
            key={alert.id}
            className={cx(
              'flex flex-col gap-4 rounded-2xl border bg-white p-4 shadow-[0_2px_8px_rgba(34,64,99,.025)] transition-colors md:flex-row md:items-center',
              alert.followed
                ? 'border-slate-200 opacity-70'
                : alert.priority === 'Alta'
                  ? 'border-red-100'
                  : 'border-slate-200/80',
            )}
            data-testid={`card-alert-${alert.id}`}
          >
            <span
              className={cx(
                'flex h-10 w-10 shrink-0 items-center justify-center rounded-xl',
                alert.priority === 'Alta'
                  ? 'bg-red-50 text-red-600'
                  : alert.priority === 'Média'
                    ? 'bg-amber-50 text-amber-600'
                    : 'bg-sky-50 text-sky-600',
              )}
            >
              {alert.priority === 'Alta' ? <AlertCircle size={18} /> : <AlertTriangle size={18} />}
            </span>
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <Link href={`/alunos/${alert.studentId}`} className="text-sm font-bold text-slate-700 hover:text-sky-700">
                  {alert.student}
                </Link>
                <PriorityBadge priority={alert.priority} />
                {alert.followed && (
                  <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700">
                    <CheckCircle2 size={13} /> Em acompanhamento
                  </span>
                )}
              </div>
              <p className="mt-1 text-xs text-slate-500">
                {alert.signal} · {alert.className}
              </p>
            </div>
            <span className="text-xs text-slate-400">{alert.date}</span>
            <button
              onClick={() => toggleAlertFollow(alert.id)}
              className={cx(
                'inline-flex h-9 items-center justify-center gap-1.5 rounded-lg border px-3 text-xs font-bold transition-colors cursor-pointer',
                alert.followed
                  ? 'border-emerald-200 text-emerald-700 hover:bg-emerald-50'
                  : 'border-slate-200 text-slate-600 hover:border-sky-300 hover:bg-sky-50 hover:text-sky-700',
              )}
              data-testid={`button-follow-alert-${alert.id}`}
            >
              {alert.followed ? <Check size={14} /> : <Bell size={14} />}
              {alert.followed ? 'Acompanhando' : 'Acompanhar'}
            </button>
          </div>
        ))}
        {filtered.length === 0 && (
          <EmptyState
            title="Nenhum alerta nesta prioridade"
            detail="Não há sinais pendentes com o filtro selecionado."
          />
        )}
      </div>
    </main>
  );
}

export function ReportsPage() {
  const [generated, setGenerated] = useState(null);
  const reports = [
    {
      title: 'Desempenho por turma',
      detail: 'Médias, evolução e distribuição de notas por turma.',
      icon: BarChart3,
    },
    {
      title: 'Frequência e acompanhamento',
      detail: 'Presença, estudantes abaixo do limite e tendências.',
      icon: CalendarDays,
    },
    {
      title: 'Mapa de atenção pedagógica',
      detail: 'Estudantes e sinais priorizados para reunião pedagógica.',
      icon: AlertTriangle,
    },
  ];

  return (
    <main className="animate-rise">
      <PageHeader
        eyebrow="Gestão"
        title="Relatórios"
        description="Gere visões objetivas para reuniões pedagógicas e acompanhamento docente."
      />
      <div className="grid gap-4 lg:grid-cols-3">
        {reports.map((report) => (
          <div
            key={report.title}
            className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_2px_8px_rgba(34,64,99,.035)]"
          >
            <span className="mb-5 inline-flex rounded-xl bg-sky-50 p-2.5 text-sky-700">
              <report.icon size={19} />
            </span>
            <h2 className="font-[var(--app-font-serif)] text-lg font-bold text-slate-800">{report.title}</h2>
            <p className="mt-2 min-h-10 text-xs leading-5 text-slate-500">{report.detail}</p>
            <div className="mt-5 flex gap-2 border-t border-slate-100 pt-4">
              <button
                onClick={() => setGenerated(report.title)}
                className="inline-flex h-9 flex-1 items-center justify-center gap-2 rounded-lg bg-sky-700 px-3 text-xs font-bold text-white hover:bg-sky-800 cursor-pointer"
                data-testid={`button-generate-${report.title.toLowerCase().replaceAll(' ', '-')}`}
              >
                <FileText size={14} />
                Gerar relatório
              </button>
              <button
                onClick={() => setGenerated(`${report.title} exportado`)}
                className="inline-flex h-9 items-center justify-center rounded-lg border border-slate-200 px-3 text-slate-600 hover:bg-slate-50 cursor-pointer"
                data-testid={`button-download-${report.title.toLowerCase().replaceAll(' ', '-')}`}
              >
                <Download size={14} />
              </button>
            </div>
          </div>
        ))}
      </div>
      {generated && (
        <div
          className="mt-5 flex items-center justify-between rounded-xl border border-emerald-100 bg-emerald-50 px-4 py-3 text-sm text-emerald-800"
          data-testid="status-report-generated"
        >
          <span className="flex items-center gap-2">
            <CheckCircle2 size={17} />
            {generated} pronto para visualização.
          </span>
          <button
            onClick={() => setGenerated(null)}
            className="rounded p-1 hover:bg-emerald-100"
            data-testid="button-close-report-status"
          >
            <X size={16} />
          </button>
        </div>
      )}
      <section className="mt-6 rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_2px_8px_rgba(34,64,99,.035)]">
        <h2 className="font-[var(--app-font-serif)] text-lg font-bold text-slate-800">Últimos relatórios</h2>
        <div className="mt-4 divide-y divide-slate-100">
          {[
            'Reunião pedagógica · Maio 2024',
            'Consolidado de frequência · 1º semestre',
            'Indicadores de desempenho · Abril 2024',
          ].map((name, index) => (
            <div key={name} className="flex items-center gap-3 py-3 first:pt-0 last:pb-0">
              <span className="rounded-lg bg-slate-100 p-2 text-slate-500">
                <FileText size={15} />
              </span>
              <div className="flex-1">
                <strong className="block text-xs text-slate-700">{name}</strong>
                <small className="text-[11px] text-slate-400">PDF · gerado {index + 1} dias atrás</small>
              </div>
              <button
                onClick={() => setGenerated(`${name} baixado em PDF`)}
                className="rounded-lg p-2 text-slate-400 hover:bg-sky-50 hover:text-sky-700"
                data-testid={`button-download-history-${index}`}
              >
                <Download size={15} />
              </button>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}

export function SettingsPage() {
  const [saved, setSaved] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  const [platformUsers, setPlatformUsers] = useState(INITIAL_PLATFORM_USERS);
  const [userModalOpen, setUserModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState(null);

  const handleToggleUserStatus = (userId) => {
    setPlatformUsers((prev) =>
      prev.map((u) => (u.id === userId ? { ...u, status: u.status === 'Ativo' ? 'Inativo' : 'Ativo' } : u)),
    );
  };

  const handleSaveUser = (savedUser) => {
    setPlatformUsers((prev) => {
      const exists = prev.some((u) => u.id === savedUser.id);
      return exists ? prev.map((u) => (u.id === savedUser.id ? savedUser : u)) : [savedUser, ...prev];
    });
  };

  return (
    <main className="animate-rise">
      <PageHeader
        eyebrow="Preferências do Ambiente"
        title="Configurações"
        description="Defina parâmetros acadêmicos e preferências para que os sinais reflitam a realidade das suas turmas."
        actions={
          saved ? (
            <span className="flex items-center gap-1.5 text-xs font-bold text-emerald-700">
              <CheckCircle2 size={16} />
              Alterações salvas
            </span>
          ) : (
            <OutlineButton
              tone="primary"
              onClick={() => {
                setSaved(true);
                setTimeout(() => setSaved(false), 2500);
              }}
              testId="button-save-settings"
            >
              Salvar alterações
            </OutlineButton>
          )
        }
      />
      <div className="grid gap-5 xl:grid-cols-[.75fr_1.25fr]">
        <aside className="space-y-2">
          <div className="rounded-2xl border border-sky-100 bg-sky-50 p-4">
            <div className="flex items-center gap-3">
              <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-sky-700 text-white">
                <UserRound size={17} />
              </span>
              <div>
                <strong className="block text-sm text-slate-800">Prof. Mariana Costa</strong>
                <span className="text-xs text-slate-500">Docente SENAI</span>
              </div>
            </div>
          </div>
          {[
            ['Perfil e instituição', UserRound],
            ['Usuários e permissões', Users],
            ['Parâmetros acadêmicos', SlidersHorizontal],
            ['Preferências de notificação', Settings],
            ['Privacidade e segurança (LGPD)', ShieldCheck],
          ].map(([label, Icon], index) => (
            <button
              key={label}
              onClick={() => setActiveTab(index)}
              className={cx(
                'flex w-full items-center gap-3 rounded-xl px-4 py-3 text-left text-sm font-semibold transition-colors cursor-pointer',
                activeTab === index ? 'bg-white text-sky-700 shadow-sm' : 'text-slate-600 hover:bg-white',
              )}
              data-testid={`button-settings-${index}`}
            >
              <Icon size={16} />
              {label}
            </button>
          ))}
        </aside>
        <div className="space-y-5">
          <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_2px_8px_rgba(34,64,99,.035)]">
            <h2 className="font-[var(--app-font-serif)] text-lg font-bold text-slate-800">Perfil e instituição</h2>
            <p className="mt-1 text-xs text-slate-500">Informações exibidas no ambiente acadêmico.</p>
            <div className="mt-5 grid gap-4 sm:grid-cols-2">
              <label className="text-xs font-bold text-slate-600">
                Nome completo
                <input
                  defaultValue="Mariana Costa"
                  className="mt-2 h-10 w-full rounded-xl border border-slate-200 px-3 text-sm font-normal outline-none focus:border-sky-500"
                  data-testid="input-settings-name"
                />
              </label>
              <label className="text-xs font-bold text-slate-600">
                E-mail institucional
                <input
                  defaultValue="mariana.costa@senai-es.org.br"
                  className="mt-2 h-10 w-full rounded-xl border border-slate-200 px-3 text-sm font-normal outline-none focus:border-sky-500"
                  data-testid="input-settings-email"
                />
              </label>
              <label className="text-xs font-bold text-slate-600 sm:col-span-2">
                Unidade
                <input
                  defaultValue="SENAI – CEP Áureo Vianna Mameri · Cachoeiro de Itapemirim – ES"
                  className="mt-2 h-10 w-full rounded-xl border border-slate-200 px-3 text-sm font-normal outline-none focus:border-sky-500"
                  data-testid="input-settings-unit"
                />
              </label>
            </div>
          </section>
          <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_2px_8px_rgba(34,64,99,.035)]">
            <div className="flex items-start gap-3">
              <span className="rounded-xl bg-amber-50 p-2 text-amber-600">
                <SlidersHorizontal size={17} />
              </span>
              <div>
                <h2 className="font-[var(--app-font-serif)] text-lg font-bold text-slate-800">Parâmetros acadêmicos</h2>
                <p className="mt-1 text-xs text-slate-500">Os parâmetros orientam a classificação dos alertas.</p>
              </div>
            </div>
            <div className="mt-5 grid gap-4 sm:grid-cols-3">
              <label className="text-xs font-bold text-slate-600">
                Frequência mínima
                <input
                  defaultValue="75"
                  type="number"
                  className="mt-2 h-10 w-full rounded-xl border border-slate-200 px-3 text-sm font-normal outline-none focus:border-sky-500"
                  data-testid="input-settings-attendance"
                />
                <small className="mt-1 block font-normal text-slate-400">percentual regimental SENAI</small>
              </label>
              <label className="text-xs font-bold text-slate-600">
                Média de atenção
                <input
                  defaultValue="6,0"
                  className="mt-2 h-10 w-full rounded-xl border border-slate-200 px-3 text-sm font-normal outline-none focus:border-sky-500"
                  data-testid="input-settings-average"
                />
                <small className="mt-1 block font-normal text-slate-400">escala de 0 a 10</small>
              </label>
              <label className="text-xs font-bold text-slate-600">
                Período vigente
                <select
                  defaultValue="1º semestre 2024"
                  className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm font-normal outline-none focus:border-sky-500"
                  data-testid="select-settings-period"
                >
                  <option>1º semestre 2024</option>
                  <option>2º semestre 2024</option>
                </select>
              </label>
            </div>
          </section>
          <UsersManagementPanel
            users={platformUsers}
            onToggleStatus={handleToggleUserStatus}
            onOpenCreate={() => {
              setEditingUser(null);
              setUserModalOpen(true);
            }}
            onOpenEdit={(user) => {
              setEditingUser(user);
              setUserModalOpen(true);
            }}
          />
          <UserFormModal
            open={userModalOpen}
            onClose={() => setUserModalOpen(false)}
            onSave={handleSaveUser}
            editingUser={editingUser}
            existingEmails={platformUsers.map((u) => u.email)}
          />
          <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_2px_8px_rgba(34,64,99,.035)]">
            <h2 className="font-[var(--app-font-serif)] text-lg font-bold text-slate-800">Privacidade e segurança (LGPD)</h2>
            <div className="mt-4 flex items-start gap-3 rounded-xl bg-slate-50 p-3 text-xs leading-5 text-slate-600">
              <LockKeyhole size={16} className="mt-0.5 shrink-0 text-sky-700" />
              Este ambiente demonstrativo usa dados fictícios locais em conformidade com a LGPD. Nenhum dado pessoal real de estudante é exposto ou compartilhado externamente.
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}

export function Login() {
  const [, setLocation] = useLocation();
  const { role, setRole } = useAcademicQueries();
  const [showPassword, setShowPassword] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [remember, setRemember] = useState(true);
  const [loading, setLoading] = useState(false);

  const selectProfile = (selectedRole) => {
    setRole(selectedRole);
    if (selectedRole === 'teacher') {
      setEmail('mariana.costa@senai-es.org.br');
    } else {
      setEmail('ana.ribeiro@aluno.senai.br');
    }
  };

  const submit = (event) => {
    event.preventDefault();
    setLoading(true);
    window.setTimeout(() => {
      setLocation(role === 'student' ? '/aluno/painel' : '/dashboard');
    }, 350);
  };

  return (
    <div className="min-h-[100dvh] overflow-hidden bg-[#f4f7fa]">
      <div className="grid min-h-[100dvh] lg:grid-cols-[minmax(390px,.83fr)_1.17fr]">
        <section className="relative hidden overflow-hidden bg-[#142e4a] px-12 py-12 text-white lg:flex lg:flex-col lg:justify-between xl:px-20">
          <div className="absolute -right-24 -top-24 h-80 w-80 rounded-full border border-white/10" />
          <div className="absolute -bottom-32 -left-28 h-96 w-96 rounded-full border border-white/10" />
          <div className="relative flex items-center gap-3">
            <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-[#1a91a6]">
              <Activity size={23} />
            </span>
            <div>
              <p className="font-[var(--app-font-serif)] text-lg font-bold">Monitoramento</p>
              <p className="text-[10px] font-semibold uppercase tracking-[.16em] text-sky-200/70">Acadêmico</p>
            </div>
          </div>
          <div className="relative max-w-lg pb-14">
            <div className="mb-7 flex items-center gap-2 text-xs font-bold uppercase tracking-[.18em] text-sky-200">
              <span className="h-px w-7 bg-sky-300" />
              SENAI · Espírito Santo
            </div>
            <h1 className="font-[var(--app-font-serif)] text-5xl font-bold leading-[1.05] tracking-[-.05em] xl:text-6xl">
              Dados que
              <br />
              <span className="text-[#62c6c9]">orientam.</span>
            </h1>
            <p className="mt-7 max-w-md text-base leading-7 text-slate-300">
              Transformar dados acadêmicos em informações úteis para apoiar decisões pedagógicas e a evolução do estudante.
            </p>
            <div className="mt-12 grid max-w-md grid-cols-3 gap-4 border-t border-white/10 pt-5">
              <div>
                <b className="block font-[var(--app-font-serif)] text-2xl">154</b>
                <span className="text-[11px] text-slate-400">alunos ativos</span>
              </div>
              <div>
                <b className="block font-[var(--app-font-serif)] text-2xl">7,6</b>
                <span className="text-[11px] text-slate-400">média geral</span>
              </div>
              <div>
                <b className="block font-[var(--app-font-serif)] text-2xl">89,4%</b>
                <span className="text-[11px] text-slate-400">frequência</span>
              </div>
            </div>
          </div>
          <p className="relative text-[11px] text-slate-400">
            SENAI – CEP Áureo Vianna Mameri
            <br />
            Cachoeiro de Itapemirim – ES
          </p>
        </section>

        <section className="flex items-center justify-center px-5 py-10 sm:px-10">
          <div className="w-full max-w-[420px]">
            <div className="mb-10 flex items-center gap-3 lg:hidden">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#142e4a] text-white">
                <Activity size={20} />
              </span>
              <div>
                <p className="font-[var(--app-font-serif)] text-base font-bold text-slate-800">Monitoramento</p>
                <p className="text-[10px] font-bold uppercase tracking-widest text-sky-700">Acadêmico</p>
              </div>
            </div>
            <div className="mb-6">
              <p className="mb-3 text-[11px] font-bold uppercase tracking-[.16em] text-sky-700">Acesso institucional</p>
              <h2 className="font-[var(--app-font-serif)] text-3xl font-bold tracking-tight text-slate-800">
                {role === 'teacher' ? 'Bem-vinda, Mariana.' : 'Olá, Ana Luísa.'}
              </h2>
              <p className="mt-2 text-sm text-slate-500">
                {role === 'teacher'
                  ? 'Entre para continuar acompanhando seus estudantes.'
                  : 'Entre para acompanhar suas notas, frequência, conquistas e oficinas.'}
              </p>
            </div>

            <div className="mb-6 grid grid-cols-2 gap-2 rounded-2xl border border-slate-200 bg-white p-1.5">
              <button
                type="button"
                onClick={() => selectProfile('teacher')}
                className={cx(
                  'flex items-center justify-center gap-2 rounded-xl py-2.5 text-xs font-bold transition-colors cursor-pointer',
                  role === 'teacher'
                    ? 'bg-[#214d75] text-white shadow-xs'
                    : 'text-slate-600 hover:bg-slate-50',
                )}
                data-testid="button-role-teacher"
              >
                <UserRound size={15} />
                Visão do Professor
              </button>
              <button
                type="button"
                onClick={() => selectProfile('student')}
                className={cx(
                  'flex items-center justify-center gap-2 rounded-xl py-2.5 text-xs font-bold transition-colors cursor-pointer',
                  role === 'student'
                    ? 'bg-[#214d75] text-white shadow-xs'
                    : 'text-slate-600 hover:bg-slate-50',
                )}
                data-testid="button-role-student"
              >
                <GraduationCap size={15} />
                Visão do Aluno
              </button>
            </div>

            <form onSubmit={submit} className="space-y-5">
              <label className="block text-xs font-bold text-slate-700">
                E-mail institucional
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder={role === 'teacher' ? 'seu.nome@senai-es.org.br' : 'aluno@senai-es.org.br'}
                  className="mt-2 h-12 w-full rounded-xl border border-slate-200 bg-white px-4 text-sm font-normal text-slate-700 outline-none transition-colors placeholder:text-slate-400 focus:border-sky-600 focus:ring-4 focus:ring-sky-100"
                  data-testid="input-email"
                />
              </label>
              <label className="block text-xs font-bold text-slate-700">
                Senha
                <div className="relative mt-2">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Digite sua senha"
                    className="h-12 w-full rounded-xl border border-slate-200 bg-white px-4 pr-12 text-sm font-normal text-slate-700 outline-none transition-colors placeholder:text-slate-400 focus:border-sky-600 focus:ring-4 focus:ring-sky-100"
                    data-testid="input-password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-3 rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                    data-testid="button-toggle-password"
                  >
                    {showPassword ? <EyeOff size={17} /> : <Eye size={17} />}
                  </button>
                </div>
              </label>
              <div className="flex items-center justify-between">
                <label className="flex cursor-pointer items-center gap-2 text-xs text-slate-600">
                  <input
                    type="checkbox"
                    checked={remember}
                    onChange={(e) => setRemember(e.target.checked)}
                    className="h-4 w-4 accent-[#214d75]"
                    data-testid="checkbox-remember"
                  />
                  Manter acesso
                </label>
                <button
                  type="button"
                  onClick={() => window.alert('Link de recuperação enviado para o e-mail institucional.')}
                  className="text-xs font-bold text-sky-700 hover:text-sky-900"
                  data-testid="button-forgot-password"
                >
                  Esqueci minha senha
                </button>
              </div>
              <button
                type="submit"
                disabled={loading}
                className="flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-[#214d75] text-sm font-bold text-white shadow-[0_5px_15px_rgba(33,77,117,.2)] transition-colors hover:bg-[#173d60] disabled:cursor-wait disabled:opacity-70 cursor-pointer"
                data-testid="button-login"
              >
                {loading
                  ? 'Entrando...'
                  : role === 'teacher'
                    ? 'Entrar como Professor'
                    : 'Entrar como Aluno'}{' '}
                {!loading && <ChevronRight size={17} />}
              </button>
            </form>
            <div className="mt-8 flex items-start gap-2 rounded-xl border border-slate-200 bg-white/70 p-3 text-[11px] leading-5 text-slate-500">
              <ShieldCheck size={15} className="mt-0.5 shrink-0 text-sky-700" />
              Ambiente seguro para uso institucional. Este demonstrador utiliza exclusivamente dados fictícios locais.
            </div>
            <p className="mt-10 text-center text-[10px] text-slate-400">© 2024 SENAI Espírito Santo · Uso interno</p>
          </div>
        </section>
      </div>
    </div>
  );
}
