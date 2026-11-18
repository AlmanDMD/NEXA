import React from 'react';
import {
  ArrowDownRight,
  ArrowUpRight,
  ClipboardList,
  X,
} from '../lib/icons';
import { Link } from '../lib/router';

export const cx = (...classes) => classes.filter(Boolean).join(' ');

export const fmt = (value) =>
  Number(value ?? 0).toLocaleString('pt-BR', {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });

export function StatusBadge({ status }) {
  const styles = {
    Regular: 'bg-emerald-50 text-emerald-700 border-emerald-100',
    Atenção: 'bg-amber-50 text-amber-700 border-amber-100',
    Crítico: 'bg-red-50 text-red-700 border-red-100',
    'Em andamento': 'bg-sky-50 text-sky-700 border-sky-100',
    Concluída: 'bg-slate-100 text-slate-600 border-slate-200',
    Respondido: 'bg-emerald-50 text-emerald-700 border-emerald-100',
    Pendente: 'bg-amber-50 text-amber-700 border-amber-100',
  };
  return (
    <span
      className={cx(
        'inline-flex items-center rounded-full border px-2.5 py-1 text-[11px] font-semibold',
        styles[status] || 'bg-slate-100 text-slate-600 border-slate-200',
      )}
      data-testid={`status-${String(status).toLowerCase().replace(' ', '-')}`}
    >
      {status}
    </span>
  );
}

export function PriorityBadge({ priority }) {
  const styles = {
    Alta: 'bg-red-50 text-red-700',
    Média: 'bg-amber-50 text-amber-700',
    Baixa: 'bg-sky-50 text-sky-700',
  };
  return (
    <span className={cx('inline-flex rounded-md px-2 py-1 text-[11px] font-bold', styles[priority] || 'bg-slate-100 text-slate-700')}>
      {priority}
    </span>
  );
}

export function MetricCard({ label, value, detail, tone = 'blue', icon: Icon, trend }) {
  const toneStyles = {
    blue: 'bg-sky-50 text-sky-700',
    green: 'bg-emerald-50 text-emerald-700',
    amber: 'bg-amber-50 text-amber-700',
    red: 'bg-red-50 text-red-700',
  };
  return (
    <div
      className="group rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_2px_8px_rgba(34,64,99,.035)] transition-transform duration-200 hover:-translate-y-0.5"
      data-testid={`metric-${String(label).toLowerCase().replaceAll(' ', '-')}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[12px] font-semibold uppercase tracking-[.08em] text-slate-500">{label}</p>
          <p className="mt-2 font-[var(--app-font-serif)] text-[29px] font-bold tracking-tight text-slate-800">{value}</p>
        </div>
        {Icon && (
          <span className={cx('rounded-xl p-2.5', toneStyles[tone] || toneStyles.blue)}>
            <Icon size={18} strokeWidth={2} />
          </span>
        )}
      </div>
      <div className="mt-3 flex items-center gap-1.5 text-xs text-slate-500">
        {trend &&
          (trend === 'up' ? (
            <ArrowUpRight size={14} className="text-emerald-600" />
          ) : (
            <ArrowDownRight size={14} className="text-red-600" />
          ))}
        <span className={trend === 'up' ? 'font-semibold text-emerald-700' : trend === 'down' ? 'font-semibold text-red-700' : ''}>
          {detail}
        </span>
      </div>
    </div>
  );
}

export function PageHeader({ eyebrow, title, description, actions }) {
  return (
    <div className="mb-7 flex flex-col justify-between gap-4 lg:flex-row lg:items-end">
      <div>
        <p className="mb-2 text-[11px] font-bold uppercase tracking-[.16em] text-sky-700">
          {eyebrow || 'Monitoramento acadêmico'}
        </p>
        <h1 className="font-[var(--app-font-serif)] text-[30px] font-bold tracking-[-.035em] text-slate-800 md:text-[34px]">
          {title}
        </h1>
        {description && <p className="mt-1.5 max-w-2xl text-sm leading-6 text-slate-500">{description}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}

export function OutlineButton({ children, onClick, icon: Icon, tone = 'default', testId, type = 'button' }) {
  return (
    <button
      type={type}
      onClick={onClick}
      className={cx(
        'inline-flex h-10 items-center justify-center gap-2 rounded-xl border px-3.5 text-sm font-semibold transition-colors cursor-pointer',
        tone === 'primary'
          ? 'border-sky-700 bg-sky-700 text-white shadow-sm hover:bg-sky-800'
          : 'border-slate-200 bg-white text-slate-700 hover:border-sky-300 hover:bg-sky-50 hover:text-sky-800',
      )}
      data-testid={testId}
    >
      {Icon && <Icon size={15} />}
      {children}
    </button>
  );
}

export function EmptyState({ title, detail }) {
  return (
    <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-14 text-center">
      <ClipboardList className="mx-auto mb-3 text-slate-300" size={32} />
      <h3 className="text-sm font-bold text-slate-700">{title}</h3>
      <p className="mx-auto mt-1 max-w-sm text-xs leading-5 text-slate-500">{detail}</p>
    </div>
  );
}

export function RequestState({ loading, error }) {
  if (!loading && !error) return null;
  return (
    <main className="animate-rise">
      <div
        className="rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm"
        role={error ? 'alert' : 'status'}
        aria-live="polite"
      >
        <div className="mx-auto max-w-md">
          <h1 className="font-[var(--app-font-serif)] text-xl font-bold text-slate-800">
            {error ? 'Não foi possível carregar os dados' : 'Carregando dados acadêmicos...'}
          </h1>
          <p className="mt-2 text-sm leading-6 text-slate-500">
            {error
              ? 'Confira se o servidor está disponível e tente novamente.'
              : 'Aguarde enquanto buscamos as informações demonstrativas no servidor.'}
          </p>
          {error && (
            <button
              onClick={() => window.location.reload()}
              className="mt-5 rounded-xl bg-sky-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-sky-800"
            >
              Tentar novamente
            </button>
          )}
        </div>
      </div>
    </main>
  );
}

export function Modal({ open, onClose, title, subtitle, children }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4 backdrop-blur-xs animate-rise">
      <div className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-6 shadow-xl">
        <div className="mb-5 flex items-start justify-between gap-3">
          <div>
            <h2 className="font-[var(--app-font-serif)] text-xl font-bold text-slate-800">{title}</h2>
            {subtitle && <p className="mt-1 text-xs text-slate-500">{subtitle}</p>}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
          >
            <X size={18} />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

export function NotFound() {
  return (
    <main className="animate-rise">
      <div className="rounded-2xl border border-slate-200/80 bg-white p-10 text-center shadow-[0_2px_8px_rgba(34,64,99,.035)]">
        <p className="text-[11px] font-bold uppercase tracking-[.16em] text-sky-700">Erro 404</p>
        <h1 className="mt-2 font-[var(--app-font-serif)] text-2xl font-bold text-slate-800">
          Página não encontrada
        </h1>
        <p className="mx-auto mt-2 max-w-md text-sm text-slate-500">
          O endereço acessado não existe ou foi movido. Utilize o menu lateral para voltar ao ambiente acadêmico.
        </p>
        <Link
          href="/dashboard"
          className="mt-6 inline-flex h-10 items-center justify-center rounded-xl bg-sky-700 px-4 text-sm font-semibold text-white hover:bg-sky-800"
        >
          Voltar ao painel principal
        </Link>
      </div>
    </main>
  );
}
