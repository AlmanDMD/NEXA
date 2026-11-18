import React from 'react';
export { EmptyState, RequestState } from '../ui-primitives';

export function SkeletonCard() {
  return (
    <div className="animate-pulse rounded-2xl border border-slate-200/80 bg-white p-5">
      <div className="h-3 w-24 rounded bg-slate-200" />
      <div className="mt-3 h-7 w-16 rounded bg-slate-200" />
      <div className="mt-4 h-2.5 w-32 rounded bg-slate-100" />
    </div>
  );
}
