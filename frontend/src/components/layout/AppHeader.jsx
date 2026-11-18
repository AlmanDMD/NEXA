import React from 'react';
import { Bell, ChevronDown, GraduationCap, Menu, UserRound } from '../../lib/icons';
import { cx } from '../ui-primitives';

export function AppHeader({ currentLabel, role, onSwitchRole, userInitials, userName, userRoleLabel, onOpenSidebar, onOpenNotifications, onOpenProfile }) {
  return (
    <header className="sticky top-0 z-20 flex h-[72px] items-center justify-between border-b border-slate-200/80 bg-[#f4f7fa]/90 px-4 backdrop-blur-md md:px-8">
      <div className="flex items-center gap-3">
        <button onClick={onOpenSidebar} className="rounded-xl p-2 text-slate-600 hover:bg-white lg:hidden">
          <Menu size={20} />
        </button>
        <div className="hidden items-center gap-2 text-xs text-slate-400 sm:flex">
          <span>Monitoramento acadêmico</span>
          <span>/</span>
          <strong className="font-semibold text-slate-600">{currentLabel}</strong>
        </div>
      </div>
      <div className="flex items-center gap-2.5">
        <div className="flex items-center rounded-xl border border-slate-200 bg-white p-1">
          <button
            type="button"
            onClick={() => onSwitchRole('teacher')}
            className={cx(
              'inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-bold transition-colors',
              role === 'teacher' ? 'bg-[#214d75] text-white' : 'text-slate-600 hover:bg-slate-50',
            )}
          >
            <UserRound size={13} />
            Professor
          </button>
          <button
            type="button"
            onClick={() => onSwitchRole('student')}
            className={cx(
              'inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-bold transition-colors',
              role === 'student' ? 'bg-[#214d75] text-white' : 'text-slate-600 hover:bg-slate-50',
            )}
          >
            <GraduationCap size={13} />
            Aluno
          </button>
        </div>
        <button onClick={onOpenNotifications} className="relative rounded-xl p-2.5 text-slate-500 hover:bg-white hover:text-sky-700">
          <Bell size={18} />
          <span className="absolute right-2 top-2 h-1.5 w-1.5 rounded-full bg-red-500 ring-2 ring-[#f4f7fa]" />
        </button>
        <div className="hidden h-7 w-px bg-slate-200 sm:block" />
        <button onClick={onOpenProfile} className="flex items-center gap-2 rounded-xl p-1.5 pr-2 hover:bg-white">
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
  );
}
