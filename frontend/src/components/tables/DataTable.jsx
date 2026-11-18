import React, { useMemo, useState } from 'react';
import { ChevronLeft, ChevronRight, Search } from '../../lib/icons';
import { EmptyState } from '../ui-primitives';

export function DataTable({ columns = [], data = [], searchPlaceholder = 'Buscar registros...', pageSize = 6 }) {
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(1);

  const filtered = useMemo(() => {
    if (!query.trim()) return data;
    const q = query.toLowerCase();
    return data.filter((row) => JSON.stringify(row).toLowerCase().includes(q));
  }, [data, query]);

  const rows = filtered.slice((page - 1) * pageSize, page * pageSize);

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-[0_2px_8px_rgba(34,64,99,.035)]">
      <div className="border-b border-slate-100 p-3">
        <div className="relative">
          <Search size={15} className="absolute left-3 top-3 text-slate-400" />
          <input
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setPage(1);
            }}
            placeholder={searchPlaceholder}
            className="h-9 w-full rounded-xl border border-slate-200 bg-slate-50 pl-9 pr-3 text-xs text-slate-700 outline-none focus:border-sky-500 focus:bg-white"
          />
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead className="border-b border-slate-100 bg-slate-50/70">
            <tr>
              {columns.map((col) => (
                <th key={col.key || col.header} className="px-5 py-3 text-[10px] font-bold uppercase tracking-[.09em] text-slate-500">
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {rows.map((row, idx) => (
              <tr key={row.id || idx} className="hover:bg-slate-50/70">
                {columns.map((col) => (
                  <td key={col.key || col.header} className="px-5 py-3.5 text-xs text-slate-700">
                    {col.render ? col.render(row) : row[col.key]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {rows.length === 0 && <EmptyState title="Nenhum registro encontrado" detail="Altere os termos da busca para visualizar resultados." />}
      <div className="flex items-center justify-between border-t border-slate-100 px-5 py-3">
        <span className="text-xs text-slate-500">{filtered.length} registros</span>
        <div className="flex items-center gap-1">
          <button disabled={page === 1} onClick={() => setPage((p) => p - 1)} className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 disabled:opacity-30">
            <ChevronLeft size={15} />
          </button>
          <span className="px-2 text-xs font-semibold text-slate-600">Página {page}</span>
          <button disabled={page * pageSize >= filtered.length} onClick={() => setPage((p) => p + 1)} className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 disabled:opacity-30">
            <ChevronRight size={15} />
          </button>
        </div>
      </div>
    </div>
  );
}
