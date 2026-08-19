import loadJson from "@/test/test";
import parseAccount from "./parseAccount";
import parseAssignments from "./parseAssignments";
import parseGdb from "./parseGdb";
import parseQuiz from "./parseQuiz";

const LMSProcessSync = async () => {
  const COOLDOWN_MINS = 1;

  console.log("[LMS Fetcher] Initialized...");

  const shouldRun = await canRunLmsFetcher(COOLDOWN_MINS);
  if (!shouldRun) {
    console.log("[LMS Fetcher] Cooldown active. Skipping execution.");
    return;
  }

  console.log("[LMS Fetcher] Cooldown passed. Executing parsers...");

  try {
    // Individual fallbacks for each module
    let assignments = {};
    let quizzes = {};
    let gdb = {};
    let accounts: AccountSummary | null = null;

    // 1. Fetch Assignments
    try {
      console.log("[LMS Fetcher] Fetching Assignments...");
      assignments = await parseAssignments();
    } catch (err) {
      console.error("[LMS Fetcher] Assignments fetch failed:", err);
    }

    // 2. Fetch Quizzes
    try {
      console.log("[LMS Fetcher] Fetching Quizzes...");
      quizzes = await parseQuiz();
    } catch (err) {
      console.error("[LMS Fetcher] Quizzes fetch failed:", err);
    }

    // 3. Fetch GDB
    try {
      console.log("[LMS Fetcher] Fetching GDB...");
      gdb = await parseGdb();
    } catch (err) {
      console.error("[LMS Fetcher] GDB fetch failed:", err);
    }

    // 4. Fetch Accounts
    try {
      console.log("[LMS Fetcher] Fetching Accounts...");
      accounts = await parseAccount();
    } catch (err) {
      console.error("[LMS Fetcher] Accounts fetch failed:", err);
    }

    console.log("[LMS Fetcher] All modules processed.");

    // Assemble unified snapshot
    const testing = false
    let freshSnapshot: LmsSnapshot;
    if (testing) {
      const data = await loadJson();

      freshSnapshot = data;

    } else {
      freshSnapshot = {
        assignments,
        quizzes,
        gdb,
        accounts,
        fetchedAt: Date.now(),
      };
    }

    // Send to Background Observer
    const response = await browser.runtime.sendMessage({
      type: "OBSERVE_LMS_DATA",
      payload: freshSnapshot,
    });

    console.log("[LMS Fetcher] Response from Background Observer:", response);

    await markLmsFetcherExecuted();
    console.log("[LMS Fetcher] Complete & Cooldown Timestamp Updated.");
  } catch (error: unknown) {
    console.error("[LMS Fetcher] Execution failed:", error);
  } finally {
    await scheduleNextAutoFetch(COOLDOWN_MINS);
  }
};

export default LMSProcessSync;
