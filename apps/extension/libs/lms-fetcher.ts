import { canRunLmsFetcher, markLmsFetcherExecuted } from "@/helper/lmsFetcherGuard";
import { scheduleNextAutoFetch } from "@/helper/lmsScheduler";
import parse_accounts from "@/utils/parse-account";
import parse_assignments from "@/utils/parse-assignments";
import parse_gdb from "@/utils/parse-gdb";
import parse_quizzes from "@/utils/parse-quiz";

const accountsStorage = storage.defineItem<AccountSummary | null>('local:accounts_data', {
    defaultValue: null,
});

const LMSProcessSync = async () => {
    const COOLDOWN_MINS = 1;

    const shouldRun = await canRunLmsFetcher(COOLDOWN_MINS);
    if (!shouldRun) {
        console.log("[LMS Fetcher] Cooldown active. Skipping execution.");
        return;
    }

    console.log("[LMS Fetcher] Cooldown passed. Executing parsers...");

    try {

        console.log('LMS Fetcher Initialized...');
        console.log('Fetching Assignments...');
        const assignments = await parse_assignments();

        console.log('Fetching Quizzes...');
        const quizzes = await parse_quizzes();

        console.log('Fetching GDB...');
        const gdb = await parse_gdb();

        console.log('Fetching Accounts...');
        const accounts = await parse_accounts();

        await browser.runtime.sendMessage({
            action: 'SYNC_ASSIGNMENTS',
            payload: assignments,
        });

        await browser.runtime.sendMessage({
            action: 'SYNC_QUIZZES',
            payload: quizzes,
        });

        await browser.runtime.sendMessage({
            action: 'SYNC_GDB',
            payload: gdb,
        });

        await browser.runtime.sendMessage({
            action: 'SYNC_ACCOUNTS',
            payload: accounts,
        });

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