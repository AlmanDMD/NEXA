import React from 'react';
import { cx } from '../ui-primitives';

export function QuickAttendanceControls({ status = 'P', onChange }) {
  const buttons = [
    { code: 'P', label: 'P · Presente', activeClass: 'bg-emerald-600 text-white border-emerald-600' },
    { code: 'F', label: 'F · Falta', activeClass: 'bg-red-600 text-white border-red-600' },
    { code: 'J', label: 'J · Justif.', activeClass: 'bg-sky-700 text-white border-sky-700' },
  ];
  return (
    <div className="flex items-center gap-1.5">
      {buttons.map((b) => (
        <button
          key={b.code}
          type="button"
          onClick={() => onChange && onChange(b.code)}
          className={cx(
            'h-9 rounded-xl border px-3 text-xs font-bold transition-colors',
            status === b.code ? b.activeClass : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50',
          )}
        >
          {b.label}
        </button>
      ))}
    </div>
  );
}
