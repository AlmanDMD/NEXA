export function createFollowUpRecord({ author = 'Prof. Mariana Costa', title, detail }) {
  return {
    date: 'Hoje',
    author,
    title,
    detail,
  };
}
