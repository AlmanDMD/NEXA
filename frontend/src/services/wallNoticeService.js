import { initialWallPosts } from '../data/academic-data';

export function filterWallPostsByClass(className) {
  if (!className || className === 'Todas as turmas') return initialWallPosts;
  return initialWallPosts.filter((p) => p.targetClass === 'Todas as turmas' || p.targetClass === className);
}
