export function getUnlockedBadgesSummary(badges = []) {
  const unlocked = badges.filter((b) => b.unlocked).length;
  return {
    unlocked,
    total: badges.length,
    percentage: badges.length ? Math.round((unlocked / badges.length) * 100) : 0,
  };
}
