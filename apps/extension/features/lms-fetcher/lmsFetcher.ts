import { canRunLmsFetcher, markLmsFetcherExecuted } from "@/utils/lmsFetcherGuard";
import { scheduleNextAutoFetch } from "@/utils/lmsScheduler";
import parseAccount from "@/features/lms-fetcher/parseAccount";
import parseAssignments from "@/features/lms-fetcher/parseAssignments";
import parseGdb from "@/features/lms-fetcher/parseGdb";
import parseQuiz from "@/features/lms-fetcher/parseQuiz";
import { observeLmsData } from "@/features/change-observer/observerEngine";


const LMSProcessSync = async () => {
    const COOLDOWN_MINS = 0.5;

    console.log('[LMS Fetcher] Initialized...');

    const shouldRun = await canRunLmsFetcher(COOLDOWN_MINS);
    if (!shouldRun) {
        console.log("[LMS Fetcher] Cooldown active. Skipping execution.");
        return;
    }

    console.log("[LMS Fetcher] Cooldown passed. Executing parsers...");

    try {
        console.log('[LMS Fetcher] Fetching all LMS modules in parallel...');

        const [assignments, quizzes, gdb, accounts] = await Promise.all([
            parseAssignments(),
            parseQuiz(),
            parseGdb(),
            parseAccount(),
        ]);

        console.log('[LMS Fetcher] All modules fetched successfully!');

        // Assemble a unified snapshot and hand it to the Observer Engine
        const freshSnapshot: LmsSnapshot = {
            assignments,
            quizzes,
            gdb,
            accounts,
            fetchedAt: Date.now(),
        };

        const result = await observeLmsData(freshSnapshot);
        console.log('[LMS Fetcher] Observer Engine result:', result);

        // Forward changes upstream (API dispatch / notifications)
        if (result.status === 'CHANGES_DETECTED') {
            await browser.runtime.sendMessage({
                action: 'OBSERVER_CHANGES',
                payload: result,
            });
        }

        await markLmsFetcherExecuted();
        console.log("[LMS Fetcher] Complete & Cooldown Timestamp Updated.");
    }
    catch (error: unknown) {
        console.error("[LMS Fetcher] Execution failed:", error);
    } finally {
        await scheduleNextAutoFetch(COOLDOWN_MINS);
    }
}

export default LMSProcessSync
