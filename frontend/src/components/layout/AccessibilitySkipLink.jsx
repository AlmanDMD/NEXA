import React, { useEffect } from 'react';
import { useLocation } from '../../lib/router';

/**
 * Componente de acessibilidade WCAG 2.1 AA (FE-049):
 * - Link "Pular para o conteúdo principal" visível ao focar via Tab
 * - Atalhos globais de teclado:
 *   Alt + 1 -> Dashboard Principal
 *   Alt + 2 -> Lista de Alunos
 *   Alt + 3 -> Diário & Chamada Rápida de Oficina
 *   Alt + 4 -> Central de Alertas
 * - Região aria-live anunciando mudanças de rota para leitores de tela
 */
export function AccessibilityController({ role = 'teacher' }) {
  const [location, setLocation] = useLocation();

  useEffect(() => {
    const handleKeyDown = (event) => {
      if (!event.altKey) return;
      if (event.key === '1') {
        event.preventDefault();
        setLocation(role === 'student' ? '/aluno/painel' : '/dashboard');
      } else if (event.key === '2') {
        event.preventDefault();
        setLocation(role === 'student' ? '/aluno/notas' : '/alunos');
      } else if (event.key === '3') {
        event.preventDefault();
        setLocation(role === 'student' ? '/aluno/autoavaliacao' : '/oficina');
      } else if (event.key === '4') {
        event.preventDefault();
        setLocation(role === 'student' ? '/aluno/ajuda' : '/alertas');
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [role, setLocation]);

  return (
    <>
      <a
        href="#conteudo-principal"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-xl focus:bg-[#142e4a] focus:px-4 focus:py-2.5 focus:text-xs focus:font-bold focus:text-white focus:shadow-lg focus:outline-2 focus:outline-offset-2 focus:outline-sky-400"
        data-testid="skip-to-content-link"
      >
        Pular para o conteúdo principal (Atalhos: Alt+1 Painel, Alt+2 Alunos/Notas, Alt+3 Oficina/Autoavaliação, Alt+4 Alertas/Ajuda)
      </a>
      <div className="sr-only" role="status" aria-live="polite" aria-atomic="true">
        Página ativa: {location}
      </div>
    </>
  );
}

export function AccessibleChartTable({ caption, headers = [], rows = [] }) {
  return (
    <table className="sr-only">
      <caption>{caption}</caption>
      <thead>
        <tr>
          {headers.map((h) => (
            <th key={h} scope="col">
              {h}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, idx) => (
          <tr key={idx}>
            {row.map((cell, cIdx) => (
              <td key={cIdx}>{cell}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
