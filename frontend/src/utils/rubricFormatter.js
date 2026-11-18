export function formatRubricCriteria(criteriaText) {
  if (!criteriaText) return ['Respeito às normas de segurança', 'Precisão técnica na execução'];
  return criteriaText.split(',').map((item) => item.trim()).filter(Boolean);
}
