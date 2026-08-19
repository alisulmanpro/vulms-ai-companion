/**
 * Observer Engine — Delta / Diff Detector
 *
 * Flow:  SyncLMS payload  →  observeLmsData()  →  ObserverResult
 *
 *  Cold start  → saves baseline, returns INITIALIZED
 *  No changes  → returns NO_DIFFERENCE  (minimal, no array noise)
 *  Changes     → returns CHANGES_DETECTED with only the diffed items
 *
 * Side-effects are intentionally isolated in `observeLmsData()`.
 * All comparison helpers below it are pure functions.
 */

import { LMS_DATA_KEY } from "@/constants/storage";

// ─── Pure Comparison Helpers ──────────────────────────────────────────────────

/**
 * Robust deep equality check that normalizes whitespace, coerces primitives (strings/numbers/booleans),
 * and ignores transient fields to eliminate false positive diffs.
 */
export const isDeepEqual = (
  a: any,
  b: any,
  ignoreKeys: Set<string> = new Set(["fetchedAt", "lastChecked", "_id"]),
): boolean => {
  if (a === b) return true;

  // Handle null / undefined cases
  if (a === null || a === undefined || b === null || b === undefined) {
    return a === b;
  }

  // Coerce primitive comparisons (e.g., handles "10" vs 10 or "true" vs true)
  if (
    (typeof a === "string" ||
      typeof a === "number" ||
      typeof a === "boolean") &&
    (typeof b === "string" || typeof b === "number" || typeof b === "boolean")
  ) {
    return String(a).trim() === String(b).trim();
  }

  if (typeof a !== "object" || typeof b !== "object") {
    return a === b;
  }

  if (a instanceof Date && b instanceof Date) {
    return a.getTime() === b.getTime();
  }

  if (Array.isArray(a) && Array.isArray(b)) {
    if (a.length !== b.length) return false;
    for (let i = 0; i < a.length; i++) {
      if (!isDeepEqual(a[i], b[i], ignoreKeys)) return false;
    }
    return true;
  }

  if (Array.isArray(a) || Array.isArray(b)) {
    return false;
  }

  const keysA = Object.keys(a).filter((k) => !ignoreKeys.has(k));
  const keysB = Object.keys(b).filter((k) => !ignoreKeys.has(k));

  if (keysA.length !== keysB.length) return false;

  for (const key of keysA) {
    if (!Object.prototype.hasOwnProperty.call(b, key)) return false;
    if (!isDeepEqual(a[key], b[key], ignoreKeys)) return false;
  }

  return true;
};

/**
 * Resolves a unique primary key per category.
 * - Quiz: quizId or courseCode + title
 * - Assignment: assignmentId or title
 * - GDB: gdbId or question
 * - Fee: challanNo
 */
const getPrimaryKeyValue = (
  item: any,
  category: ObservedDiff["category"],
  courseCode?: string,
): string => {
  const course = String(item.courseCode || courseCode || "").trim();

  if (category === "quiz") {
    if (item.quizId) return String(item.quizId).trim();

    const srNo = item.srNo ? String(item.srNo).trim() : "";
    return `${course}_sr${srNo}`;
  }
  if (category === "assignment") {
    if (item.assignmentId) return String(item.assignmentId).trim();

    const srNo = item.srNo ? String(item.srNo).trim() : "";
    return `${course}_sr${srNo}`;
  }
  if (category === "gdb") {
    if (item.gdbId) return String(item.gdbId).trim();

    const srNo = item.srNo ? String(item.srNo).trim() : "";
    return `${course}_sr${srNo}`;
  }
  if (category === "fee") {
    const challanNo = item.challanNo ? String(item.challanNo).trim() : "";
    return `${course}_challan${challanNo}`;
  }
  return "";
};

/**
 * Compares two flat arrays by category-specific unique keys.
 * Emits ONLY 'ADDED', 'UPDATED', or 'REMOVED' events.
 */
const diffItemArray = <T extends object>(
  oldList: T[],
  newList: T[],
  category: ObservedDiff["category"],
  courseCode?: string,
): ObservedDiff<T>[] => {
  const diffs: ObservedDiff<T>[] = [];

  const oldMap = new Map<string, T>();
  for (const item of oldList) {
    const key = getPrimaryKeyValue(item, category, courseCode);
    if (key) oldMap.set(key, item);
  }

  const newMap = new Map<string, T>();
  for (const item of newList) {
    const key = getPrimaryKeyValue(item, category, courseCode);
    if (key) newMap.set(key, item);
  }

  // 1. ADDED & UPDATED Check
  for (const [id, newItem] of newMap) {
    const oldItem = oldMap.get(id);

    if (oldItem === undefined) {
      diffs.push({
        category,
        eventType: "ADDED",
        courseCode,
        details: newItem,
      });
    } else if (!isDeepEqual(oldItem, newItem)) {
      diffs.push({
        category,
        eventType: "UPDATED",
        courseCode,
        details: newItem,
      });
    }
  }

  // 2. REMOVED Check
  for (const [id, oldItem] of oldMap) {
    if (!newMap.has(id)) {
      diffs.push({
        category,
        eventType: "REMOVED",
        courseCode,
        details: oldItem,
      });
    }
  }

  return diffs;
};

/**
 * Diffs all courses for a course-keyed category.
 */
const diffCourseMap = <T extends object>(
  oldData: Record<string, T[]>,
  newData: Record<string, T[]>,
  category: ObservedDiff["category"],
): ObservedDiff<T>[] => {
  const allCourses = new Set([
    ...Object.keys(oldData),
    ...Object.keys(newData),
  ]);

  const diffs: ObservedDiff<T>[] = [];

  for (const courseCode of allCourses) {
    const oldList = oldData[courseCode] ?? [];
    const newList = newData[courseCode] ?? [];
    const courseDiffs = diffItemArray(oldList, newList, category, courseCode);
    diffs.push(...courseDiffs);
  }

  return diffs;
};

/**
 * Diffs the flat challans list inside AccountSummary.
 */
const diffChallans = (
  oldAccounts: AccountSummary | null,
  newAccounts: AccountSummary | null,
): ObservedDiff<Challan>[] => {
  const oldList = oldAccounts?.challansList ?? [];
  const newList = newAccounts?.challansList ?? [];
  return diffItemArray<Challan>(oldList, newList, "fee");
};

/**
 * Computes all differences between two LmsSnapshot objects.
 * Returns an array of differences containing 'SAME', 'ADDED', 'UPDATED', or 'REMOVED' events.
 */
export const computeLmsDiff = (
  stored: LmsSnapshot,
  fresh: LmsSnapshot,
): ObservedDiff<object>[] => [
  ...diffCourseMap<Quiz>(stored.quizzes, fresh.quizzes, "quiz"),
  ...diffCourseMap<Assignment>(
    stored.assignments,
    fresh.assignments,
    "assignment",
  ),
  ...diffCourseMap<GDB>(stored.gdb, fresh.gdb, "gdb"),
  ...diffChallans(stored.accounts, fresh.accounts),
];

// ─── Main Observer Engine (with Storage Side-Effects) ─────────────────────────

/**
 * Runs the full Observer pipeline:
 *
 *  1. Reads `local:lms_data` from Extension Storage.
 *  2. Cold-start → saves baseline, returns INITIALIZED.
 *  3. Existing baseline → diffs fresh vs stored.
 *     - No changes → returns NO_DIFFERENCE.
 *     - Changes    → overwrites baseline, returns CHANGES_DETECTED.
 *
 * @param freshSnapshot  The fully assembled LmsSnapshot from SyncLMS parsers.
 * @returns              A strictly-typed ObserverResult ready for notification
 *                       dispatch or API forwarding.
 */
export const observeLmsData = async (
  freshSnapshot: LmsSnapshot,
): Promise<ObserverResult> => {
  // Step 1 — Read stored baseline
  const storedSnapshot = await storage.getItem<LmsSnapshot>(LMS_DATA_KEY);

  // Step 2 — Cold Start: no baseline exists yet
  if (!storedSnapshot) {
    console.log("[Observer Engine] Cold start — saving initial baseline.");
    await storage.setItem(LMS_DATA_KEY, freshSnapshot);

    return {
      status: "INITIALIZED",
      message: "Initial storage baseline set.",
      differences: [],
    } satisfies ObserverInitialized;
  }

  // Step 3 — Compare fresh data against stored baseline
  console.log(
    "[Observer Engine] Comparing fresh snapshot against stored baseline...",
  );
  const allDifferences = computeLmsDiff(storedSnapshot, freshSnapshot);

  // Step 4 — Always update the baseline after comparison
  await storage.setItem(LMS_DATA_KEY, freshSnapshot);
  console.log("[Observer Engine] Baseline updated in storage.");

  // Step 5 — Return structured result
  if (allDifferences.length === 0) {
    console.log("[Observer Engine] No changes detected.");
    return {
      status: "NO_DIFFERENCE",
      message: "All items are identical. No state change detected.",
      differences: [],
    } satisfies ObserverNoDifference;
  }

  console.log(`[Observer Engine] ${allDifferences.length} change(s) detected.`);
  allDifferences.forEach(({ eventType, category, courseCode, details }) => {
    const course = courseCode ? `[${courseCode}] ` : "";
    // Surface a human-readable label from the details object
    const label =
      (details as Record<string, unknown>)["title"] ??
      (details as Record<string, unknown>)["question"] ??
      (details as Record<string, unknown>)["challanNo"] ??
      JSON.stringify(details);
    console.log(`  → ${eventType}: ${course}${category} — "${label}"`);
  });

  return {
    status: "CHANGES_DETECTED",
    timestamp: Date.now(),
    differences: allDifferences,
  } satisfies ObserverChangesDetected;
};
