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

// ─── Storage Key ──────────────────────────────────────────────────────────────

const LMS_DATA_KEY = 'local:lms_data' as const;

// ─── Pure Comparison Helpers ──────────────────────────────────────────────────

/**
 * Compares two flat arrays by a chosen primary-key field.
 * Returns only the changed items as `ObservedDiff` entries.
 * No storage access; no side-effects.
 */
const diffItemArray = <T extends object>(
    oldList: T[],
    newList: T[],
    keyField: keyof T,
    category: ObservedDiff['category'],
    courseCode?: string
): ObservedDiff<T>[] => {
    const diffs: ObservedDiff<T>[] = [];

    const oldMap = new Map<unknown, T>(
        oldList.map((item) => [item[keyField], item])
    );
    const newMap = new Map<unknown, T>(
        newList.map((item) => [item[keyField], item])
    );

    // ADDED + UPDATED — iterate over fresh data
    for (const [id, newItem] of newMap) {
        const oldItem = oldMap.get(id);

        if (oldItem === undefined) {
            diffs.push({ category, eventType: 'ADDED', courseCode, details: newItem });
        } else if (JSON.stringify(oldItem) !== JSON.stringify(newItem)) {
            diffs.push({ category, eventType: 'UPDATED', courseCode, details: newItem });
        }
    }

    // REMOVED — items in storage no longer present in fresh data
    for (const [id, oldItem] of oldMap) {
        if (!newMap.has(id)) {
            diffs.push({ category, eventType: 'REMOVED', courseCode, details: oldItem });
        }
    }

    return diffs;
};

/**
 * Diffs all courses for a course-keyed category
 * (assignments, quizzes, or gdbs).
 */
const diffCourseMap = <T extends object>(
    oldData: Record<string, T[]>,
    newData: Record<string, T[]>,
    keyField: keyof T,
    category: ObservedDiff['category']
): ObservedDiff<T>[] => {
    const allCourses = new Set([
        ...Object.keys(oldData),
        ...Object.keys(newData),
    ]);

    const diffs: ObservedDiff<T>[] = [];

    for (const courseCode of allCourses) {
        const oldList = oldData[courseCode] ?? [];
        const newList = newData[courseCode] ?? [];
        const courseDiffs = diffItemArray(oldList, newList, keyField, category, courseCode);
        diffs.push(...courseDiffs);
    }

    return diffs;
};

/**
 * Diffs the flat challans list inside AccountSummary.
 * `challanNo` is the stable primary key for fee challans.
 */
const diffChallans = (
    oldAccounts: AccountSummary | null,
    newAccounts: AccountSummary | null
): ObservedDiff<Challan>[] => {
    const oldList = oldAccounts?.challansList ?? [];
    const newList = newAccounts?.challansList ?? [];
    return diffItemArray<Challan>(oldList, newList, 'challanNo', 'fee');
};

/**
 * Pure function: computes all differences between two LmsSnapshot objects.
 * Returns an empty array when the snapshots are identical.
 *
 * Primary keys used:
 *  • Quizzes      → `title`       (natural identity on VU LMS)
 *  • Assignments  → `title`       (natural identity on VU LMS)
 *  • GDBs         → `question`    (natural identity on VU LMS)
 *  • Fee Challans → `challanNo`   (server-issued unique key)
 */
export const computeLmsDiff = (
    stored: LmsSnapshot,
    fresh: LmsSnapshot
): ObservedDiff<object>[] => [
    ...diffCourseMap<Quiz>(stored.quizzes, fresh.quizzes, 'title', 'quiz'),
    ...diffCourseMap<Assignment>(stored.assignments, fresh.assignments, 'title', 'assignment'),
    ...diffCourseMap<GDB>(stored.gdb, fresh.gdb, 'question', 'gdb'),
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
    freshSnapshot: LmsSnapshot
): Promise<ObserverResult> => {

    // Step 1 — Read stored baseline
    const storedSnapshot = await storage.getItem<LmsSnapshot>(LMS_DATA_KEY);

    // Step 2 — Cold Start: no baseline exists yet
    if (!storedSnapshot) {
        console.log('[Observer Engine] Cold start — saving initial baseline.');
        await storage.setItem(LMS_DATA_KEY, freshSnapshot);

        return {
            status: 'INITIALIZED',
            message: 'Initial storage baseline set.',
            differences: [],
        } satisfies ObserverInitialized;
    }

    // Step 3 — Compare fresh data against stored baseline
    console.log('[Observer Engine] Comparing fresh snapshot against stored baseline...');
    const differences = computeLmsDiff(storedSnapshot, freshSnapshot);

    // Step 4 — Always update the baseline after comparison
    await storage.setItem(LMS_DATA_KEY, freshSnapshot);
    console.log('[Observer Engine] Baseline updated in storage.');

    // Step 5 — Return structured result
    if (differences.length === 0) {
        console.log('[Observer Engine] No changes detected.');
        return {
            status: 'NO_DIFFERENCE',
            message: 'No new changes detected.',
        } satisfies ObserverNoDifference;
    }

    console.log(`[Observer Engine] ${differences.length} change(s) detected.`);
    differences.forEach(({ eventType, category, courseCode, details }) => {
        const course = courseCode ? `[${courseCode}] ` : '';
        // Surface a human-readable label from the details object
        const label =
            (details as Record<string, unknown>)['title']
            ?? (details as Record<string, unknown>)['question']
            ?? (details as Record<string, unknown>)['challanNo']
            ?? JSON.stringify(details);
        console.log(`  → ${eventType}: ${course}${category} — "${label}"`);
    });

    return {
        status: 'CHANGES_DETECTED',
        timestamp: Date.now(),
        differences,
    } satisfies ObserverChangesDetected;
};
