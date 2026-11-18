import React from 'react';
import { Check } from '../../lib/icons';
import { cx } from '../ui-primitives';

export function QuickPracticalCheckGrid({ students = [], completedIds = [], onToggle }) {
  return (
    <div className="grid gap-2.5 sm:grid-cols-2 lg:grid-cols-3">
      {students.map((student) => {
        const done = completedIds.includes(student.id);
        return (
          <button
            key={student.id}
            type="button"
            onClick={() => onToggle && onToggle(student.id)}
            className={cx(
              'flex items-center justify-between rounded-xl border p-3 text-left transition-all',
              done ? 'border-emerald-200 bg-emerald-50/70 text-emerald-900' : 'border-slate-200 bg-white text-slate-700',
            )}
          >
            <div>
              <strong className="block text-xs font-bold">{student.name}</strong>
              <span className="text-[11px] opacity-75">#{student.registration}</span>
            </div>
            <span className={cx('flex h-7 w-7 items-center justify-center rounded-lg', done ? 'bg-emerald-600 text-white' : 'bg-slate-100 text-slate-400')}>
              <Check size={14} />
            </span>
          </button>
        );
      })}
    </div>
  );
}
