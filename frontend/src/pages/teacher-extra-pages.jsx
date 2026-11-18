import React, { useMemo, useState } from 'react';
import {
  AlertTriangle,
  Bell,
  CalendarDays,
  Check,
  CheckCircle2,
  CircleHelp,
  ClipboardCheck,
  ClipboardList,
  MessageSquare,
  Plus,
  Send,
  ShieldCheck,
  Users,
  Wrench,
} from '../lib/icons';
import { Link } from '../lib/router';
import { useAcademicQueries } from '../context/AcademicContext';
import {
  cx,
  EmptyState,
  fmt,
  MetricCard,
  Modal,
  OutlineButton,
  PageHeader,
  PriorityBadge,
  StatusBadge,
} from '../components/ui-primitives';

export function WorkshopDiaryPage() {
  const {
    students: studentsQuery,
    classes: classesQuery,
    attendanceMap,
    setStudentAttendanceStatus,
    markAllPresentInClass,
    workshopModules,
    practicalActivities,
    togglePracticalCompletion,
    addPracticalActivity,
  } = useAcademicQueries();

  const students = studentsQuery.data ?? [];
  const classes = classesQuery.data ?? [];
  const [selectedClass, setSelectedClass] = useState('Todas');
  const [activeTab, setActiveTab] = useState('chamada'); // 'chamada' | 'oficina'
  const [savedBanner, setSavedBanner] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [actTitle, setActTitle] = useState('');
  const [actClass, setActClass] = useState('Eletrotécnica 2A');
  const [actCriteria, setActCriteria] = useState('');
  const [actDue, setActDue] = useState('Hoje · Laboratório SENAI');

  const classStudents = useMemo(
    () =>
      students.filter(
        (student) => selectedClass === 'Todas' || student.className === selectedClass,
      ),
    [students, selectedClass],
  );

  const presentCount = classStudents.filter((s) => (attendanceMap[s.id] || 'P') === 'P').length;
  const absentCount = classStudents.filter((s) => attendanceMap[s.id] === 'F').length;
  const justifiedCount = classStudents.filter((s) => attendanceMap[s.id] === 'J').length;
  const belowLimitCount = classStudents.filter((s) => s.attendance < 75).length;

  const filteredActivities = useMemo(
    () =>
      practicalActivities.filter(
        (act) => selectedClass === 'Todas' || act.className === selectedClass,
      ),
    [practicalActivities, selectedClass],
  );

  const handleCreateActivity = (event) => {
    event.preventDefault();
    if (!actTitle.trim()) return;
    addPracticalActivity({
      title: actTitle.trim(),
      className: actClass,
      criteria: actCriteria.trim() || 'Precisão técnica, organização da bancada e segurança.',
      dueDate: actDue.trim(),
    });
    setActTitle('');
    setActCriteria('');
    setModalOpen(false);
  };

  return (
    <main className="animate-rise">
      <PageHeader
        eyebrow="Operação Docente · Sala e Laboratório"
        title="Diário & Oficina Prática"
        description="Realize a chamada rápida em 1 clique e registre a conclusão das atividades práticas de bancada."
        actions={
          <>
            <select
              value={selectedClass}
              onChange={(e) => setSelectedClass(e.target.value)}
              className="h-10 rounded-xl border border-slate-200 bg-white px-3 text-sm font-medium text-slate-700 outline-none focus:border-sky-500"
              data-testid="select-workshop-class"
            >
              <option value="Todas">Todas as turmas</option>
              {classes.map((c) => (
                <option key={c.id} value={c.name}>
                  {c.name}
                </option>
              ))}
            </select>
            {activeTab === 'chamada' ? (
              <OutlineButton
                icon={CheckCircle2}
                tone="primary"
                onClick={() => {
                  markAllPresentInClass(selectedClass);
                  setSavedBanner(true);
                  setTimeout(() => setSavedBanner(false), 2500);
                }}
                testId="button-mark-all-present"
              >
                Marcar todos presentes
              </OutlineButton>
            ) : (
              <OutlineButton
                icon={Plus}
                tone="primary"
                onClick={() => setModalOpen(true)}
                testId="button-new-practical-activity"
              >
                Nova prática de oficina
              </OutlineButton>
            )}
          </>
        }
      />

      {savedBanner && (
        <div className="mb-5 flex items-center justify-between rounded-xl border border-emerald-100 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          <span className="flex items-center gap-2 font-semibold">
            <CheckCircle2 size={17} />
            Frequência do diário sincronizada com sucesso.
          </span>
        </div>
      )}

      <div className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Presentes hoje"
          value={`${presentCount} / ${classStudents.length}`}
          detail={`${justifiedCount} justificativa(s) registrada(s)`}
          icon={ClipboardCheck}
          tone="green"
          trend="up"
        />
        <MetricCard
          label="Ausentes na aula"
          value={String(absentCount)}
          detail="Clique em P, F ou J para atualizar"
          icon={CalendarDays}
          tone={absentCount > 0 ? 'amber' : 'blue'}
        />
        <MetricCard
          label="Alerta regimental (<75%)"
          value={String(belowLimitCount)}
          detail="Limite mínimo exigido pelo SENAI"
          icon={AlertTriangle}
          tone={belowLimitCount > 0 ? 'red' : 'green'}
        />
        <MetricCard
          label="Módulos de oficina"
          value={String(workshopModules.length)}
          detail={`${practicalActivities.length} atividades práticas ativas`}
          icon={Wrench}
          tone="blue"
        />
      </div>

      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setActiveTab('chamada')}
            className={cx(
              'inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-xs font-bold transition-colors cursor-pointer',
              activeTab === 'chamada'
                ? 'bg-sky-700 text-white shadow-xs'
                : 'bg-white text-slate-600 hover:bg-slate-100',
            )}
            data-testid="tab-quick-attendance"
          >
            <CalendarDays size={15} />
            Chamada Rápida em 1 Clique
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('oficina')}
            className={cx(
              'inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-xs font-bold transition-colors cursor-pointer',
              activeTab === 'oficina'
                ? 'bg-sky-700 text-white shadow-xs'
                : 'bg-white text-slate-600 hover:bg-slate-100',
            )}
            data-testid="tab-practical-activities"
          >
            <Wrench size={15} />
            Módulos & Registro Rápido de Bancada
          </button>
        </div>

        <button
          type="button"
          onClick={() => {
            setSavedBanner(true);
            setTimeout(() => setSavedBanner(false), 2500);
          }}
          className="inline-flex h-9 items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3.5 text-xs font-bold text-slate-700 hover:border-sky-300 hover:bg-sky-50 hover:text-sky-800 cursor-pointer"
        >
          <Check size={14} />
          Salvar diário da aula
        </button>
      </div>

      {activeTab === 'chamada' ? (
        <div className="overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-[0_2px_8px_rgba(34,64,99,.035)]">
          <div className="border-b border-slate-100 bg-slate-50/70 px-5 py-3.5 flex flex-wrap items-center justify-between gap-2">
            <div>
              <h2 className="font-[var(--app-font-serif)] text-base font-bold text-slate-800">
                Lista de Presença e Termômetro Regimental (75%)
              </h2>
              <p className="text-xs text-slate-500">
                Marque Presente (P), Falta (F) ou Falta Justificada (J) diretamente em cada estudante.
              </p>
            </div>
            <span className="rounded-lg bg-sky-50 px-2.5 py-1 text-[11px] font-bold text-sky-800">
              Aula de Hoje · Turno Regular
            </span>
          </div>
          <div className="divide-y divide-slate-100">
            {classStudents.map((student, idx) => {
              const currentStatus = attendanceMap[student.id] || 'P';
              const isBelow75 = student.attendance < 75;
              const isNear75 = student.attendance >= 75 && student.attendance < 80;
              return (
                <div
                  key={student.id}
                  className="flex flex-col justify-between gap-4 px-5 py-4 transition-colors hover:bg-slate-50/70 md:flex-row md:items-center"
                  data-testid={`row-attendance-${student.id}`}
                >
                  <div className="flex items-center gap-3.5">
                    <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-sky-50 text-xs font-bold text-sky-800">
                      {student.name
                        .split(' ')
                        .map((n) => n[0])
                        .slice(0, 2)
                        .join('')}
                    </span>
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <Link
                          href={`/alunos/${student.id}`}
                          className="text-sm font-bold text-slate-700 hover:text-sky-700"
                        >
                          {student.name}
                        </Link>
                        <span className="rounded-md bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-500">
                          Bancada {String(idx + 1).padStart(2, '0')}
                        </span>
                        {isBelow75 && (
                          <span className="inline-flex items-center gap-1 rounded-full bg-red-50 px-2 py-0.5 text-[10px] font-bold text-red-700">
                            <AlertTriangle size={11} /> Crítico (&lt;75%)
                          </span>
                        )}
                        {isNear75 && (
                          <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-bold text-amber-700">
                            Atenção ao limite
                          </span>
                        )}
                      </div>
                      <p className="mt-0.5 text-xs text-slate-400">
                        #{student.registration} · {student.className}
                      </p>
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center gap-5">
                    <div className="w-40">
                      <div className="mb-1 flex justify-between text-[11px]">
                        <span className="text-slate-500">Assiduidade</span>
                        <strong
                          className={cx(
                            isBelow75
                              ? 'text-red-600'
                              : isNear75
                                ? 'text-amber-600'
                                : 'text-slate-700',
                          )}
                        >
                          {student.attendance}%
                        </strong>
                      </div>
                      <div className="h-1.5 overflow-hidden rounded-full bg-slate-100">
                        <div
                          className={cx(
                            'h-full rounded-full',
                            isBelow75
                              ? 'bg-red-500'
                              : isNear75
                                ? 'bg-amber-400'
                                : 'bg-emerald-500',
                          )}
                          style={{ width: `${student.attendance}%` }}
                        />
                      </div>
                    </div>

                    <div className="flex items-center gap-1.5">
                      {[
                        { code: 'P', label: 'P · Presente', activeClass: 'bg-emerald-600 text-white border-emerald-600' },
                        { code: 'F', label: 'F · Falta', activeClass: 'bg-red-600 text-white border-red-600' },
                        { code: 'J', label: 'J · Justif.', activeClass: 'bg-sky-700 text-white border-sky-700' },
                      ].map((btn) => (
                        <button
                          key={btn.code}
                          type="button"
                          onClick={() => setStudentAttendanceStatus(student.id, btn.code)}
                          className={cx(
                            'h-9 rounded-xl border px-3 text-xs font-bold transition-colors cursor-pointer',
                            currentStatus === btn.code
                              ? btn.activeClass
                              : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50',
                          )}
                          data-testid={`btn-attendance-${student.id}-${btn.code}`}
                        >
                          {btn.label}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        <div className="space-y-5">
          <div className="grid gap-4 lg:grid-cols-3">
            {workshopModules.map((mod) => (
              <div
                key={mod.id}
                className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_2px_8px_rgba(34,64,99,.035)]"
              >
                <div className="flex items-center justify-between">
                  <span className="rounded-lg bg-sky-50 px-2.5 py-1 text-[11px] font-bold text-sky-700">
                    {mod.code}
                  </span>
                  <span className="text-xs font-semibold text-slate-400">{mod.workload}</span>
                </div>
                <h3 className="mt-3 font-[var(--app-font-serif)] text-base font-bold text-slate-800">
                  {mod.name}
                </h3>
                <p className="mt-1 text-xs text-slate-500">
                  {mod.className} · {mod.lab}
                </p>
                <div className="mt-4 flex items-center gap-2 rounded-xl bg-slate-50 px-3 py-2 text-[11px] font-semibold text-slate-600">
                  <ShieldCheck size={14} className="text-sky-700 shrink-0" />
                  {mod.safetyNorm}
                </div>
              </div>
            ))}
          </div>

          <div className="space-y-4">
            {filteredActivities.map((act) => {
              const targetStudents = students.filter((s) => s.className === act.className);
              const completedCount = targetStudents.filter((s) =>
                act.completedStudentIds.includes(s.id),
              ).length;
              return (
                <section
                  key={act.id}
                  className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_2px_8px_rgba(34,64,99,.035)]"
                >
                  <div className="flex flex-col justify-between gap-3 border-b border-slate-100 pb-4 md:flex-row md:items-center">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="rounded-md bg-sky-50 px-2.5 py-0.5 text-[11px] font-bold text-sky-700">
                          {act.className}
                        </span>
                        <span className="text-xs text-slate-400">{act.dueDate}</span>
                      </div>
                      <h3 className="mt-1.5 font-[var(--app-font-serif)] text-lg font-bold text-slate-800">
                        {act.title}
                      </h3>
                      <p className="mt-1 text-xs text-slate-500">
                        <strong className="text-slate-600">Rubrica / Critérios:</strong> {act.criteria}
                      </p>
                    </div>
                    <div className="text-left md:text-right">
                      <span className="text-xs font-bold text-sky-700">
                        {completedCount} de {targetStudents.length} concluíram
                      </span>
                      <div className="mt-1.5 h-2 w-36 overflow-hidden rounded-full bg-slate-100">
                        <div
                          className="h-full rounded-full bg-sky-700"
                          style={{
                            width: `${targetStudents.length ? (completedCount / targetStudents.length) * 100 : 0}%`,
                          }}
                        />
                      </div>
                    </div>
                  </div>

                  <p className="mt-4 mb-2.5 text-[11px] font-bold uppercase tracking-wider text-slate-400">
                    Registro rápido de conclusão na bancada (clique para validar)
                  </p>
                  <div className="grid gap-2.5 sm:grid-cols-2 lg:grid-cols-3">
                    {targetStudents.map((student) => {
                      const done = act.completedStudentIds.includes(student.id);
                      return (
                        <button
                          key={student.id}
                          type="button"
                          onClick={() => togglePracticalCompletion(act.id, student.id)}
                          className={cx(
                            'flex items-center justify-between rounded-xl border p-3 text-left transition-all cursor-pointer',
                            done
                              ? 'border-emerald-200 bg-emerald-50/70 text-emerald-900'
                              : 'border-slate-200 bg-white text-slate-700 hover:border-sky-200 hover:bg-slate-50',
                          )}
                          data-testid={`btn-practical-${act.id}-${student.id}`}
                        >
                          <div className="min-w-0 pr-2">
                            <strong className="block truncate text-xs font-bold">{student.name}</strong>
                            <span className="text-[11px] opacity-75">#{student.registration}</span>
                          </div>
                          <span
                            className={cx(
                              'flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-xs font-bold',
                              done ? 'bg-emerald-600 text-white' : 'bg-slate-100 text-slate-400',
                            )}
                          >
                            <Check size={14} />
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </section>
              );
            })}
          </div>
        </div>
      )}

      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title="Nova atividade prática de oficina"
        subtitle="Cadastre uma tarefa prática de bancada para acompanhamento rápido durante a aula."
      >
        <form onSubmit={handleCreateActivity} className="space-y-4">
          <label className="block text-xs font-bold text-slate-700">
            Título da atividade prática
            <input
              required
              value={actTitle}
              onChange={(e) => setActTitle(e.target.value)}
              placeholder="Ex: Montagem e Teste de Partida Estrela-Triângulo"
              className="mt-1.5 h-10 w-full rounded-xl border border-slate-200 px-3 text-sm font-normal outline-none focus:border-sky-500"
            />
          </label>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="block text-xs font-bold text-slate-700">
              Turma
              <select
                value={actClass}
                onChange={(e) => setActClass(e.target.value)}
                className="mt-1.5 h-10 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm font-normal outline-none focus:border-sky-500"
              >
                {classes.map((c) => (
                  <option key={c.id} value={c.name}>
                    {c.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="block text-xs font-bold text-slate-700">
              Prazo / Bancada
              <input
                value={actDue}
                onChange={(e) => setActDue(e.target.value)}
                className="mt-1.5 h-10 w-full rounded-xl border border-slate-200 px-3 text-sm font-normal outline-none focus:border-sky-500"
              />
            </label>
          </div>
          <label className="block text-xs font-bold text-slate-700">
            Critérios de avaliação e segurança (Rubrica)
            <textarea
              rows={3}
              value={actCriteria}
              onChange={(e) => setActCriteria(e.target.value)}
              placeholder="Ex: Respeito à NR-10, precisão da montagem e funcionamento do circuito..."
              className="mt-1.5 w-full rounded-xl border border-slate-200 p-3 text-sm font-normal outline-none focus:border-sky-500"
            />
          </label>
          <div className="flex justify-end gap-2 pt-2">
            <OutlineButton onClick={() => setModalOpen(false)}>Cancelar</OutlineButton>
            <OutlineButton type="submit" tone="primary">
              Publicar atividade prática
            </OutlineButton>
          </div>
        </form>
      </Modal>
    </main>
  );
}

export function TeacherCommunicationPage() {
  const { helpRequests, replyHelpRequest, wallPosts, addWallPost, classes: classesQuery } =
    useAcademicQueries();
  const classes = classesQuery.data ?? [];
  const [replyDrafts, setReplyDrafts] = useState({});
  const [postModalOpen, setPostModalOpen] = useState(false);
  const [postTitle, setPostTitle] = useState('');
  const [postContent, setPostContent] = useState('');
  const [postTarget, setPostTarget] = useState('Todas as turmas');
  const [postTag, setPostTag] = useState('Importante');

  const pendingCount = helpRequests.filter((r) => r.status === 'Pendente').length;

  const handleSendReply = (reqId) => {
    const text = (replyDrafts[reqId] || '').trim();
    if (!text) return;
    replyHelpRequest(reqId, text);
    setReplyDrafts((prev) => ({ ...prev, [reqId]: '' }));
  };

  const handleCreatePost = (event) => {
    event.preventDefault();
    if (!postTitle.trim() || !postContent.trim()) return;
    addWallPost({
      title: postTitle.trim(),
      content: postContent.trim(),
      targetClass: postTarget,
      tag: postTag,
    });
    setPostTitle('');
    setPostContent('');
    setPostModalOpen(false);
  };

  return (
    <main className="animate-rise">
      <PageHeader
        eyebrow="Comunicação Docente"
        title="Mural & Pedidos de Ajuda"
        description="Responda às solicitações enviadas pelos estudantes nas bancadas e publique comunicados para as turmas."
        actions={
          <OutlineButton
            icon={Plus}
            tone="primary"
            onClick={() => setPostModalOpen(true)}
            testId="button-new-wall-post"
          >
            Publicar aviso no mural
          </OutlineButton>
        }
      />

      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        <MetricCard
          label="Pedidos pendentes"
          value={String(pendingCount)}
          detail="Aguardando orientação docente"
          icon={CircleHelp}
          tone={pendingCount > 0 ? 'amber' : 'green'}
        />
        <MetricCard
          label="Total de solicitações"
          value={String(helpRequests.length)}
          detail="Dúvidas técnicas de aula e oficina"
          icon={MessageSquare}
          tone="blue"
        />
        <MetricCard
          label="Avisos publicados"
          value={String(wallPosts.length)}
          detail="Visíveis no painel dos estudantes"
          icon={Bell}
          tone="green"
        />
      </div>

      <div className="grid gap-5 xl:grid-cols-[1.2fr_.8fr]">
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-[var(--app-font-serif)] text-lg font-bold text-slate-800">
                Solicitações de ajuda dos estudantes
              </h2>
              <p className="text-xs text-slate-500">
                Chamados abertos durante as aulas teóricas e práticas de laboratório
              </p>
            </div>
          </div>

          {helpRequests.map((req) => (
            <div
              key={req.id}
              className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_2px_8px_rgba(34,64,99,.035)]"
              data-testid={`card-help-request-${req.id}`}
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex flex-wrap items-center gap-2">
                  <Link
                    href={`/alunos/${req.studentId}`}
                    className="text-sm font-bold text-slate-800 hover:text-sky-700"
                  >
                    {req.studentName}
                  </Link>
                  <PriorityBadge priority={req.urgency} />
                  <StatusBadge status={req.status} />
                </div>
                <span className="text-xs text-slate-400">{req.createdAt}</span>
              </div>
              <p className="mt-1 text-xs font-semibold text-sky-700">
                {req.className} · {req.subject} · {req.bench}
              </p>
              <p className="mt-3 rounded-xl bg-slate-50 p-3 text-xs leading-5 text-slate-700">
                "{req.question}"
              </p>

              {req.reply ? (
                <div className="mt-3 rounded-xl border border-emerald-100 bg-emerald-50/60 p-3 text-xs text-emerald-900">
                  <strong className="block font-bold text-emerald-800">
                    Sua orientação registrada:
                  </strong>
                  <p className="mt-1 leading-5">{req.reply}</p>
                </div>
              ) : (
                <div className="mt-3 flex gap-2">
                  <input
                    value={replyDrafts[req.id] || ''}
                    onChange={(e) =>
                      setReplyDrafts((prev) => ({ ...prev, [req.id]: e.target.value }))
                    }
                    placeholder="Escreva uma orientação ou confirme o atendimento na bancada..."
                    className="h-10 flex-1 rounded-xl border border-slate-200 px-3 text-xs outline-none focus:border-sky-500"
                  />
                  <button
                    type="button"
                    onClick={() => handleSendReply(req.id)}
                    className="inline-flex h-10 items-center gap-1.5 rounded-xl bg-sky-700 px-3.5 text-xs font-bold text-white hover:bg-sky-800 cursor-pointer"
                  >
                    <Send size={13} />
                    Responder
                  </button>
                </div>
              )}
            </div>
          ))}
        </section>

        <section className="space-y-4">
          <div>
            <h2 className="font-[var(--app-font-serif)] text-lg font-bold text-slate-800">
              Mural de avisos das turmas
            </h2>
            <p className="text-xs text-slate-500">
              Comunicados oficiais exibidos na visão de todos os estudantes
            </p>
          </div>

          {wallPosts.map((post) => (
            <div
              key={post.id}
              className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_2px_8px_rgba(34,64,99,.035)]"
            >
              <div className="flex items-center justify-between gap-2">
                <span className="rounded-md bg-sky-50 px-2.5 py-0.5 text-[11px] font-bold text-sky-700">
                  {post.tag} · {post.targetClass}
                </span>
                <span className="text-xs text-slate-400">{post.date}</span>
              </div>
              <h3 className="mt-2.5 font-[var(--app-font-serif)] text-base font-bold text-slate-800">
                {post.title}
              </h3>
              <p className="mt-1.5 text-xs leading-5 text-slate-600">{post.content}</p>
              <p className="mt-3 text-[11px] font-semibold text-slate-400">
                Publicado por {post.author}
              </p>
            </div>
          ))}
        </section>
      </div>

      <Modal
        open={postModalOpen}
        onClose={() => setPostModalOpen(false)}
        title="Publicar comunicado no mural"
        subtitle="O aviso ficará imediatamente visível para os estudantes da turma selecionada."
      >
        <form onSubmit={handleCreatePost} className="space-y-4">
          <label className="block text-xs font-bold text-slate-700">
            Título do comunicado
            <input
              required
              value={postTitle}
              onChange={(e) => setPostTitle(e.target.value)}
              placeholder="Ex: Orientações para a Avaliação Prática de Laboratório"
              className="mt-1.5 h-10 w-full rounded-xl border border-slate-200 px-3 text-sm font-normal outline-none focus:border-sky-500"
            />
          </label>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="block text-xs font-bold text-slate-700">
              Turma destinatária
              <select
                value={postTarget}
                onChange={(e) => setPostTarget(e.target.value)}
                className="mt-1.5 h-10 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm font-normal outline-none focus:border-sky-500"
              >
                <option>Todas as turmas</option>
                {classes.map((c) => (
                  <option key={c.id} value={c.name}>
                    {c.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="block text-xs font-bold text-slate-700">
              Categoria
              <select
                value={postTag}
                onChange={(e) => setPostTag(e.target.value)}
                className="mt-1.5 h-10 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm font-normal outline-none focus:border-sky-500"
              >
                <option>Importante</option>
                <option>Oficina</option>
                <option>Avaliação</option>
              </select>
            </label>
          </div>
          <label className="block text-xs font-bold text-slate-700">
            Mensagem
            <textarea
              required
              rows={4}
              value={postContent}
              onChange={(e) => setPostContent(e.target.value)}
              placeholder="Escreva o conteúdo completo do comunicado para os estudantes..."
              className="mt-1.5 w-full rounded-xl border border-slate-200 p-3 text-sm font-normal outline-none focus:border-sky-500"
            />
          </label>
          <div className="flex justify-end gap-2 pt-2">
            <OutlineButton onClick={() => setPostModalOpen(false)}>Cancelar</OutlineButton>
            <OutlineButton type="submit" tone="primary">
              Publicar no mural
            </OutlineButton>
          </div>
        </form>
      </Modal>
    </main>
  );
}
