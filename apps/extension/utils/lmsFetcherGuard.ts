const lastFetchItem = storage.defineItem<number>(
  "local:vuext_last_fetch_timestamp",
  {
    defaultValue: 0,
  },
);

export const canRunLmsFetcher = async (
  cooldownMinutes = 1,
): Promise<boolean> => {
  const lastFetchTime = await lastFetchItem.getValue();
  if (!lastFetchTime) return true;

  const timePassed = Date.now() - lastFetchTime;

  // 3 seconds Grace Buffer taake 59.8s par bhi condition match ho jaye
  const COOLDOWN_MS = cooldownMinutes * 60 * 1000 - 3000;

  return timePassed >= COOLDOWN_MS;
};

export const markLmsFetcherExecuted = async (): Promise<void> => {
  await lastFetchItem.setValue(Date.now());
};
