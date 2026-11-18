import React, { useState } from 'react';
import {
  Activity,
  Award,
  BarChart3,
  Bell,
  BookOpen,
  CalendarDays,
  ChevronDown,
  CircleHelp,
  FileBarChart,
  FileText,
  GraduationCap,
  LayoutDashboard,
  LogOut,
  Menu,
  MessageSquare,
  PanelLeftClose,
  PanelLeftOpen,
  Settings,
  UserRound,
  Users,
  Wrench,
  X,
} from './lib/icons';
import { Link, Route, Router as WouterRouter, Switch, useLocation } from './lib/router';
import { AcademicDataProvider, useAcademicQueries } from './context/AcademicContext';
import { cx, NotFound } from './components/ui-primitives';
import {
  AlertsPage,
  AnalysisPage,
  ClassesPage,
  Dashboard,
  Login,
  ReportsPage,
  SettingsPage,
  StudentDetail,
  StudentsPage,
  SubjectsPage,
} from './pages/replit-pages';
import {
  TeacherCommunicationPage,
  WorkshopDiaryPage,
} from './pages/teacher-extra-pages';
import {
  StudentDashboardPage,
  StudentGradesReportPage,
  StudentSelfAssessmentPage,
  StudentSupportPage,
} from './pages/student-pages';

const teacherNavGroups = [
  {
    label: 'Visão geral',
    items: [{ href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard }],
  },
  {
    label: 'Acompanhamento',
    items: [
      { href: '/alunos', label: 'Alunos', icon: Users },
      { href: '/turmas', label: 'Turmas', icon: GraduationCap },
      { href: '/disciplinas', label: 'Disciplinas', icon: BookOpen },
      { href: '/oficina', label: 'Diário & Oficina', icon: Wrench },
      { href: '/desempenho', label: 'Desempenho', icon: BarChart3 },
      { href: '/frequencia', label: 'Frequência', icon: CalendarDays },
    ],
  },
  {
    label: 'Gestão & Suporte',
    items: [
      { href: '/alertas', label: 'Alertas', icon: Bell, badge: 'alerts' },
      { href: '/comunicacao', label: 'Mural & Ajuda', icon: MessageSquare, badge: 'help' },
      { href: '/relatorios', label: 'Relatórios', icon: FileBarChart },
    ],
  },
];

const studentNavGroups = [
  {
    label: 'Portal do Aluno',
    items: [
      { href: '/aluno/painel', label: 'Meu Desempenho', icon: LayoutDashboard },
      { href: '/aluno/notas', label: 'Notas & Boletim', icon: FileText },
      { href: '/aluno/autoavaliacao', label: 'Autoavaliação & Conquistas', icon: Award },
      { href: '/aluno/ajuda', label: 'Mural & Pedir Ajuda', icon: CircleHelp },
    ],
  },
];

function Sidebar({ open, onClose, collapsed, onCollapse }) {
  const [location, setLocation] = useLocation();
  const { role, setRole, activeStudent, alerts, helpRequests } = useAcademicQueries();

  const navGroups = role === 'student' ? studentNavGroups : teacherNavGroups;
  const openAlertsCount = (alerts?.data || []).filter((a) => !a.followed).length;
  const pendingHelpCount = (helpRequests || []).filter((h) => h.status === 'Pendente').length;

  const userInitials =
    role === 'student'
      ? activeStudent.name
          .split(' ')
          .map((n) => n[0])
          .slice(0, 2)
          .join('')
      : 'MC';
  const userName = role === 'student' ? activeStudent.name : 'Mariana Costa';
  const userSubtitle =
    role === 'student' ? `Aluno · ${activeStudent.className}` : 'Professor · SENAI';

  return (
    <>
      <div
        onClick={onClose}
        className={cx(
          'fixed inset-0 z-30 bg-slate-900/30 backdrop-blur-sm transition-opacity lg:hidden',
          open ? 'opacity-100' : 'pointer-events-none opacity-0',
        )}
      />
      <aside
        className={cx(
          'fixed inset-y-0 left-0 z-40 flex w-[260px] flex-col bg-[#142e4a] text-white shadow-xl transition-transform duration-300 lg:translate-x-0',
          open ? 'translate-x-0' : '-translate-x-full',
          collapsed && 'lg:w-[76px]',
        )}
      >
        <div
          className={cx(
            'flex h-[88px] items-center border-b border-white/10 px-5',
            collapsed && 'lg:justify-center lg:px-0',
          )}
        >
          <div className="flex items-center gap-3 overflow-hidden">
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#1a91a6] shadow-[0_5px_18px_rgba(26,145,166,.25)]">
              <Activity size={21} />
            </span>
            {!collapsed && (
              <div className="min-w-0">
                <p className="font-[var(--app-font-serif)] text-[15px] font-bold tracking-tight">
                  Monitoramento
                </p>
                <p className="text-[10px] font-semibold uppercase tracking-[.14em] text-sky-200/70">
                  Acadêmico · NEXA
                </p>
              </div>
            )}
          </div>
          <button
            onClick={onClose}
            className="ml-auto rounded-lg p-2 text-slate-300 hover:bg-white/10 lg:hidden"
            data-testid="button-close-sidebar"
          >
            <X size={18} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-3 py-6 scrollbar-thin">
          <div className="mb-5 rounded-xl border border-white/10 bg-white/[.06] p-3">
            <div className={cx('flex items-center gap-3', collapsed && 'lg:justify-center')}>
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-sky-100 text-xs font-bold text-sky-900">
                {userInitials}
              </span>
              {!collapsed && (
                <div className="min-w-0">
                  <p className="truncate text-xs font-bold">{userName}</p>
                  <p className="truncate pt-0.5 text-[10px] text-slate-300">{userSubtitle}</p>
                </div>
              )}
            </div>
          </div>

          {navGroups.map((group) => (
            <div key={group.label} className="mb-6">
              <p
                className={cx(
                  'mb-2 px-3 text-[10px] font-bold uppercase tracking-[.15em] text-slate-400/80',
                  collapsed && 'lg:hidden',
                )}
              >
                {group.label}
              </p>
              {group.items.map((item) => {
                const active =
                  location === item.href ||
                  (item.href === '/alunos' && location.startsWith('/alunos/'));
                const badgeCount =
                  item.badge === 'alerts'
                    ? openAlertsCount
                    : item.badge === 'help'
                      ? pendingHelpCount
                      : 0;
                return (
                  <Link
                    href={item.href}
                    onClick={onClose}
                    key={item.href}
                    className={cx(
                      'mb-1 flex items-center gap-3 rounded-xl px-3 py-2.5 text-[13px] font-semibold transition-colors',
                      active
                        ? 'bg-[#1a91a6] text-white shadow-sm'
                        : 'text-slate-300 hover:bg-white/[.08] hover:text-white',
                      collapsed && 'lg:justify-center lg:px-0',
                    )}
                    data-testid={`link-nav-${item.label.toLowerCase().replaceAll(' ', '-')}`}
                  >
                    <item.icon size={17} strokeWidth={active ? 2.4 : 1.8} />
                    {!collapsed && <span className="truncate">{item.label}</span>}
                    {badgeCount > 0 && !collapsed && (
                      <span className="ml-auto rounded-md bg-red-400/20 px-1.5 py-0.5 text-[10px] font-bold text-red-200">
                        {badgeCount}
                      </span>
                    )}
                  </Link>
                );
              })}
            </div>
          ))}
        </div>

        <div className="border-t border-white/10 p-3 space-y-1">
          {role === 'teacher' && (
            <Link
              href="/configuracoes"
              onClick={onClose}
              className={cx(
                'flex items-center gap-3 rounded-xl px-3 py-2.5 text-[13px] font-semibold transition-colors',
                location === '/configuracoes'
                  ? 'bg-[#1a91a6] text-white shadow-sm'
                  : 'text-slate-300 hover:bg-white/[.08] hover:text-white',
                collapsed && 'lg:justify-center lg:px-0',
              )}
              data-testid="link-nav-configuracoes"
            >
              <Settings size={17} />
              {!collapsed && 'Configurações'}
            </Link>
          )}
          <button
            type="button"
            onClick={() => {
              onClose();
              setLocation('/');
            }}
            className={cx(
              'flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-[13px] font-semibold text-slate-300 hover:bg-white/[.08] hover:text-white cursor-pointer',
              collapsed && 'lg:justify-center lg:px-0',
            )}
            data-testid="button-logout-sidebar"
          >
            <LogOut size={17} />
            {!collapsed && 'Sair / Tela de Login'}
          </button>
          <button
            type="button"
            onClick={onCollapse}
            className="hidden w-full items-center gap-3 rounded-xl px-3 py-2.5 text-[13px] font-semibold text-slate-400 hover:bg-white/[.08] hover:text-white lg:flex cursor-pointer"
            data-testid="button-collapse-sidebar"
          >
            {collapsed ? <PanelLeftOpen size={17} /> : <PanelLeftClose size={17} />}
            {!collapsed && 'Recolher menu'}
          </button>
        </div>
      </aside>
    </>
  );
}

function AppShell() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const [location, setLocation] = useLocation();
  const { role, setRole, activeStudent } = useAcademicQueries();

  const allNavItems = [...teacherNavGroups, ...studentNavGroups].flatMap((group) => group.items);
  const current = allNavItems.find(
    (item) =>
      item.href === location || (item.href === '/alunos' && location.startsWith('/alunos/')),
  );

  const switchRole = (nextRole) => {
    setRole(nextRole);
    if (nextRole === 'student') {
      setLocation('/aluno/painel');
    } else {
      setLocation('/dashboard');
    }
  };

  const userInitials =
    role === 'student'
      ? activeStudent.name
          .split(' ')
          .map((n) => n[0])
          .slice(0, 2)
          .join('')
      : 'MC';
  const userName = role === 'student' ? activeStudent.name : 'Mariana Costa';
  const userRoleLabel = role === 'student' ? 'Aluno SENAI' : 'Professor SENAI';

  return (
    <div className="min-h-[100dvh] bg-[#f4f7fa]">
      <Sidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        collapsed={collapsed}
        onCollapse={() => setCollapsed(!collapsed)}
      />
      <div
        className={cx(
          'min-h-[100dvh] transition-[padding] duration-300 lg:pl-[260px]',
          collapsed && 'lg:pl-[76px]',
        )}
      >
        <header className="sticky top-0 z-20 flex h-[72px] items-center justify-between border-b border-slate-200/80 bg-[#f4f7fa]/90 px-4 backdrop-blur-md md:px-8">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="rounded-xl p-2 text-slate-600 hover:bg-white lg:hidden"
              data-testid="button-open-sidebar"
            >
              <Menu size={20} />
            </button>
            <div className="hidden items-center gap-2 text-xs text-slate-400 sm:flex">
              <span>Monitoramento acadêmico</span>
              <span>/</span>
              <strong className="font-semibold text-slate-600">
                {current?.label ||
                  (location.startsWith('/alunos/')
                    ? 'Perfil do aluno'
                    : location === '/configuracoes'
                      ? 'Configurações'
                      : 'Página')}
              </strong>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <div className="flex items-center rounded-xl border border-slate-200 bg-white p-1">
              <button
                type="button"
                onClick={() => switchRole('teacher')}
                className={cx(
                  'inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-bold transition-colors cursor-pointer',
                  role === 'teacher'
                    ? 'bg-[#214d75] text-white'
                    : 'text-slate-600 hover:bg-slate-50',
                )}
                data-testid="header-switch-teacher"
              >
                <UserRound size={13} />
                Professor
              </button>
              <button
                type="button"
                onClick={() => switchRole('student')}
                className={cx(
                  'inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-bold transition-colors cursor-pointer',
                  role === 'student'
                    ? 'bg-[#214d75] text-white'
                    : 'text-slate-600 hover:bg-slate-50',
                )}
                data-testid="header-switch-student"
              >
                <GraduationCap size={13} />
                Aluno
              </button>
            </div>

            <button
              onClick={() =>
                setLocation(role === 'student' ? '/aluno/ajuda' : '/alertas')
              }
              className="relative rounded-xl p-2.5 text-slate-500 hover:bg-white hover:text-sky-700 cursor-pointer"
              data-testid="button-header-notifications"
            >
              <Bell size={18} />
              <span className="absolute right-2 top-2 h-1.5 w-1.5 rounded-full bg-red-500 ring-2 ring-[#f4f7fa]" />
            </button>

            <div className="hidden h-7 w-px bg-slate-200 sm:block" />

            <button
              onClick={() =>
                setLocation(role === 'student' ? '/aluno/painel' : '/configuracoes')
              }
              className="flex items-center gap-2 rounded-xl p-1.5 pr-2 hover:bg-white cursor-pointer"
              data-testid="button-header-profile"
            >
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-sky-100 text-[11px] font-bold text-sky-800">
                {userInitials}
              </span>
              <span className="hidden text-left sm:block">
                <strong className="block text-xs text-slate-700">{userName}</strong>
                <small className="text-[10px] text-slate-400">{userRoleLabel}</small>
              </span>
              <ChevronDown size={14} className="hidden text-slate-400 sm:block" />
            </button>
          </div>
        </header>

        <div className="mx-auto max-w-[1500px] px-4 py-7 md:px-8 md:py-9">
          <Switch>
            {/* Visão do Professor (8 páginas originais do Replit + 2 páginas complementares) */}
            <Route path="/dashboard" component={Dashboard} />
            <Route path="/alunos/:id" component={StudentDetail} />
            <Route path="/alunos" component={StudentsPage} />
            <Route path="/turmas" component={ClassesPage} />
            <Route path="/disciplinas" component={SubjectsPage} />
            <Route path="/oficina" component={WorkshopDiaryPage} />
            <Route path="/desempenho" component={() => <AnalysisPage kind="desempenho" />} />
            <Route path="/frequencia" component={() => <AnalysisPage kind="frequencia" />} />
            <Route path="/alertas" component={AlertsPage} />
            <Route path="/comunicacao" component={TeacherCommunicationPage} />
            <Route path="/relatorios" component={ReportsPage} />
            <Route path="/configuracoes" component={SettingsPage} />

            {/* Visão do Aluno (+4 páginas no mesmo estilo visual do Replit) */}
            <Route path="/aluno/painel" component={StudentDashboardPage} />
            <Route path="/aluno/notas" component={StudentGradesReportPage} />
            <Route path="/aluno/autoavaliacao" component={StudentSelfAssessmentPage} />
            <Route path="/aluno/ajuda" component={StudentSupportPage} />

            <Route component={NotFound} />
          </Switch>
        </div>
      </div>
    </div>
  );
}

function AppContent() {
  const [location] = useLocation();
  if (location === '/' || location === '/login') {
    return <Login />;
  }
  return <AppShell />;
}

export default function App() {
  return (
    <AcademicDataProvider>
      <WouterRouter>
        <AppContent />
      </WouterRouter>
    </AcademicDataProvider>
  );
}
