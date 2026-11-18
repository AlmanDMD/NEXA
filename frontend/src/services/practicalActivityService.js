import { initialPracticalActivities } from '../data/academic-data';

export function getPracticalActivitiesByClass(className) {
  if (!className || className === 'Todas') return initialPracticalActivities;
  return initialPracticalActivities.filter((item) => item.className === className);
}
