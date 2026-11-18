export function filterStudentsList(students = [], { search = '', status = 'Todos', className = 'Todas as turmas' } = {}) {
  const q = search.trim().toLowerCase();
  return students.filter(
    (s) =>
      (status === 'Todos' || s.status === status) &&
      (className === 'Todas as turmas' || s.className === className) &&
      (!q || `${s.name} ${s.registration} ${s.className}`.toLowerCase().includes(q)),
  );
}
