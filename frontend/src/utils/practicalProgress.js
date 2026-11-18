export function calculatePracticalCompletionRate(completedCount, totalStudents) {
  if (!totalStudents || totalStudents <= 0) return 0;
  return Math.round((completedCount / totalStudents) * 100);
}
