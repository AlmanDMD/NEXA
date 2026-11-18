import React from 'react';
import { LockKeyhole } from '../../lib/icons';

export function LgpdNoticeBanner() {
  return (
    <div className="flex items-start gap-3 rounded-xl bg-slate-50 p-3 text-xs leading-5 text-slate-600">
      <LockKeyhole size={16} className="mt-0.5 shrink-0 text-sky-700" />
      <span>
        Este ambiente demonstrativo utiliza exclusivamente dados fictícios locais em conformidade com a LGPD.
      </span>
    </div>
  );
}
