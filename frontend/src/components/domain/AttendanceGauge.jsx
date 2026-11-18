import React from 'react';
import { cx } from '../ui-primitives';

export function AttendanceGauge({ attendance = 90 }) {
  const isBelow75 = attendance < 75;
  const isNear75 = attendance >= 75 && attendance < 80;
  return (
    <div className="w-full">
      <div className="mb-1 flex justify-between text-xs">
        <span className="text-slate-500">Frequência acumulada</span>
        <strong className={cx(isBelow75 ? 'text-red-600' : isNear75 ? 'text-amber-600' : 'text-slate-700')}>
          {attendance}%
        </strong>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-slate-100">
        <div
          className={cx('h-full rounded-full', isBelow75 ? 'bg-red-500' : isNear75 ? 'bg-amber-400' : 'bg-emerald-500')}
          style={{ width: `${attendance}%` }}
        />
      </div>
    </div>
  );
}
