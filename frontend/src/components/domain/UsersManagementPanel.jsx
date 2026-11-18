import React, { useMemo, useState } from 'react';
import { CheckCircle2, Filter, Plus, Search, ShieldCheck, Users } from '../../lib/icons';
import { cx, EmptyState, OutlineButton, StatusBadge } from '../ui-primitives';
import { ConfirmDialog } from '../ui/Modal';

export const INITIAL_PLATFORM_USERS = [
  {
    id: 'u-01',
    name: 'Mariana Costa',
    email: 'mariana.costa@senai-es.org.br',
    registration: 'DOC-2021.045',
    role: 'Professor',
    unit: 'CEP Áureo Vianna Mameri',
    phone: '(28) 99912-3401',
    status: 'Ativo',
  },
  {
    id: 'u-02',
    name: 'Marcos Vinícius Tavares',
    email: 'marcos.tavares@senai-es.org.br',
    registration: 'DOC-2019.018',
    role: 'Professor',
    unit: 'CEP Áureo Vianna Mameri',
    phone: '(28) 99844-1120',
    status: 'Ativo',
  },
  {
    id: 'u-03',
    name: 'Juliana F. Rocha',
    email: 'juliana.rocha@senai-es.org.br',
    registration: 'DOC-2022.073',
    role: 'Professor',
    unit: 'CEP Áureo Vianna Mameri',
    phone: '(28) 99715-8890',
    status: 'Ativo',
  },
  {
    id: 'u-04',
    name: 'Ana Luísa Ribeiro',
    email: 'ana.ribeiro@aluno.senai.br',
    registration: '2024.0187',
    role: 'Aluno',
    unit: 'Eletrotécnica 2A',
    phone: '(28) 99901-2233',
    status: 'Ativo',
  },
  {
    id: 'u-05',
    name: 'Bruno Henrique Alves',
    email: 'bruno.alves@aluno.senai.br',
    registration: '2024.0214',
    role: 'Aluno',
    unit: 'Mecânica 1B',
    phone: '(28) 99823-4511',
    status: 'Ativo',
  },
  {
    id: 'u-06',
    name: 'Daniel Souza Martins',
    email: 'daniel.martins@aluno.senai.br',
    registration: '2024.0302',
    role: 'Aluno',
    unit: 'Informática 1A',
    phone: '(28) 99776-0912',
    status: 'Inativo',
  },
];

export function UsersManagementPanel({ users = INITIAL_PLATFORM_USERS, onToggleStatus, onOpenCreate, onOpenEdit }) {
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('Todos');
  const [confirmUser, setConfirmUser] = useState(null);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return users.filter(
      (u) =>
        (roleFilter === 'Todos' || u.role === roleFilter) &&
        (!q || `${u.name} ${u.email} ${u.registration}`.toLowerCase().includes(q)),
    );
  }, [users, search, roleFilter]);

  return (
    <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_2px_8px_rgba(34,64,99,.035)]">
      <div className="mb-4 flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
        <div>
          <h2 className="font-[var(--app-font-serif)] text-lg font-bold text-slate-800">
            Gestão de Usuários e Acessos
          </h2>
          <p className="mt-1 text-xs text-slate-500">
            Consulte e gerencie o acesso de professores e alunos cadastrados na plataforma.
          </p>
        </div>
        {onOpenCreate && (
          <OutlineButton icon={Plus} tone="primary" onClick={onOpenCreate} testId="button-new-user">
            Novo usuário
          </OutlineButton>
        )}
      </div>

      <div className="mb-4 flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search size={15} className="absolute left-3 top-3 text-slate-400" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar por nome, e-mail institucional ou matrícula..."
            className="h-10 w-full rounded-xl border border-slate-200 bg-slate-50 pl-9 pr-3 text-xs text-slate-700 outline-none focus:border-sky-500 focus:bg-white"
            data-testid="input-search-users"
          />
        </div>
        <div className="flex gap-2">
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            className="h-10 rounded-xl border border-slate-200 bg-white px-3 text-xs font-semibold text-slate-600 outline-none focus:border-sky-500"
            data-testid="select-user-role-filter"
          >
            <option value="Todos">Todos os perfis</option>
            <option value="Professor">Professores</option>
            <option value="Aluno">Alunos</option>
          </select>
          <button
            type="button"
            onClick={() => {
              setSearch('');
              setRoleFilter('Todos');
            }}
            className="inline-flex h-10 items-center gap-1.5 rounded-xl border border-slate-200 px-3 text-xs font-semibold text-slate-600 hover:bg-slate-50"
          >
            <Filter size={14} />
            Limpar
          </button>
        </div>
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-100">
        <table className="w-full min-w-[680px] text-left">
          <thead className="border-b border-slate-100 bg-slate-50/70">
            <tr>
              {['Usuário', 'Matrícula SENAI', 'Papel', 'Status', 'Ações'].map((head) => (
                <th key={head} className="px-4 py-3 text-[10px] font-bold uppercase tracking-[.09em] text-slate-500">
                  {head}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {filtered.map((user) => (
              <tr key={user.id} className="hover:bg-slate-50/70" data-testid={`row-user-${user.id}`}>
                <td className="px-4 py-3.5">
                  <div className="flex items-center gap-3">
                    <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-sky-50 text-xs font-bold text-sky-800">
                      {user.name
                        .split(' ')
                        .map((n) => n[0])
                        .slice(0, 2)
                        .join('')}
                    </span>
                    <div>
                      <strong className="block text-xs font-bold text-slate-800">{user.name}</strong>
                      <span className="text-[11px] text-slate-500">{user.email}</span>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3.5 text-xs font-semibold text-slate-600">{user.registration}</td>
                <td className="px-4 py-3.5">
                  <span
                    className={cx(
                      'inline-flex rounded-full px-2.5 py-0.5 text-[11px] font-bold',
                      user.role === 'Professor' ? 'bg-sky-50 text-sky-700' : 'bg-emerald-50 text-emerald-700',
                    )}
                  >
                    {user.role}
                  </span>
                </td>
                <td className="px-4 py-3.5">
                  <StatusBadge status={user.status === 'Ativo' ? 'Regular' : 'Crítico'} />
                  <span className="ml-1.5 text-[11px] font-semibold text-slate-600">{user.status}</span>
                </td>
                <td className="px-4 py-3.5">
                  <div className="flex items-center gap-2">
                    {onOpenEdit && (
                      <button
                        type="button"
                        onClick={() => onOpenEdit(user)}
                        className="rounded-lg border border-slate-200 px-2.5 py-1 text-[11px] font-bold text-slate-600 hover:border-sky-300 hover:bg-sky-50 hover:text-sky-700"
                        data-testid={`button-edit-user-${user.id}`}
                      >
                        Editar
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={() => setConfirmUser(user)}
                      className={cx(
                        'rounded-lg border px-2.5 py-1 text-[11px] font-bold',
                        user.status === 'Ativo'
                          ? 'border-red-200 text-red-600 hover:bg-red-50'
                          : 'border-emerald-200 text-emerald-700 hover:bg-emerald-50',
                      )}
                      data-testid={`button-toggle-user-${user.id}`}
                    >
                      {user.status === 'Ativo' ? 'Desativar' : 'Ativar'}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {filtered.length === 0 && (
        <div className="mt-3">
          <EmptyState
            title="Nenhum usuário encontrado"
            detail="Verifique o termo pesquisado ou altere o filtro de perfil institucional."
          />
        </div>
      )}

      <ConfirmDialog
        open={Boolean(confirmUser)}
        onClose={() => setConfirmUser(null)}
        onConfirm={() => {
          if (confirmUser && onToggleStatus) {
            onToggleStatus(confirmUser.id);
          }
        }}
        title={confirmUser?.status === 'Ativo' ? 'Confirmar desativação de acesso' : 'Reativar conta de usuário'}
        description={
          confirmUser
            ? `Tem certeza que deseja ${confirmUser.status === 'Ativo' ? 'desativar' : 'reativar'} o acesso de ${confirmUser.name} (${confirmUser.email})?`
            : ''
        }
        confirmLabel={confirmUser?.status === 'Ativo' ? 'Sim, desativar' : 'Sim, reativar'}
      />
    </section>
  );
}
