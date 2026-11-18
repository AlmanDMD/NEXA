import React, { useId, useState } from 'react';
import { Eye, EyeOff } from '../../lib/icons';
import { cx } from '../ui-primitives';

export function InputText({ label, error, className = '', ...props }) {
  const id = useId();
  return (
    <label htmlFor={id} className="block text-xs font-bold text-slate-700">
      {label}
      <input
        id={id}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? `${id}-error` : undefined}
        className={cx(
          'mt-1.5 h-10 w-full rounded-xl border bg-white px-3 text-sm font-normal text-slate-700 outline-none transition-colors focus:border-sky-500',
          error ? 'border-red-400' : 'border-slate-200',
          className,
        )}
        {...props}
      />
      {error && (
        <span id={`${id}-error`} className="mt-1 block text-[11px] font-medium text-red-600">
          {error}
        </span>
      )}
    </label>
  );
}

export function InputPassword({ label = 'Senha', error, ...props }) {
  const id = useId();
  const [visible, setVisible] = useState(false);
  return (
    <label htmlFor={id} className="block text-xs font-bold text-slate-700">
      {label}
      <div className="relative mt-1.5">
        <input
          id={id}
          type={visible ? 'text' : 'password'}
          aria-invalid={Boolean(error)}
          className={cx(
            'h-10 w-full rounded-xl border bg-white px-3 pr-10 text-sm font-normal text-slate-700 outline-none focus:border-sky-500',
            error ? 'border-red-400' : 'border-slate-200',
          )}
          {...props}
        />
        <button
          type="button"
          onClick={() => setVisible((v) => !v)}
          className="absolute right-2.5 top-2 rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
        >
          {visible ? <EyeOff size={16} /> : <Eye size={16} />}
        </button>
      </div>
      {error && <span className="mt-1 block text-[11px] font-medium text-red-600">{error}</span>}
    </label>
  );
}

export function SelectField({ label, children, error, ...props }) {
  const id = useId();
  return (
    <label htmlFor={id} className="block text-xs font-bold text-slate-700">
      {label}
      <select
        id={id}
        aria-invalid={Boolean(error)}
        className="mt-1.5 h-10 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm font-normal text-slate-700 outline-none focus:border-sky-500"
        {...props}
      >
        {children}
      </select>
    </label>
  );
}
