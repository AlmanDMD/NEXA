import React from 'react';
import { Star } from '../../lib/icons';
import { cx } from '../ui-primitives';

export function StudentBadgeCard({ badge }) {
  return (
    <div className={cx('rounded-xl border p-4', badge.unlocked ? 'border-sky-100 bg-sky-50/40' : 'border-slate-200 bg-slate-50/60 opacity-75')}>
      <div className="flex items-center gap-2.5">
        <span className={cx('flex h-9 w-9 items-center justify-center rounded-xl', badge.unlocked ? 'bg-sky-700 text-white' : 'bg-slate-200 text-slate-500')}>
          <Star size={16} />
        </span>
        <div>
          <strong className="block text-xs font-bold text-slate-800">{badge.title}</strong>
          <span className="text-[11px] font-semibold text-sky-700">
            {badge.unlocked ? 'Conquista desbloqueada' : `Em progresso (${badge.progress}%)`}
          </span>
        </div>
      </div>
      <p className="mt-2 text-xs leading-5 text-slate-600">{badge.description}</p>
    </div>
  );
}
