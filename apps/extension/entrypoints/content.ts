import LMSProcessSync from "@/features/lms-fetcher/lmsFetcher";

export default defineContentScript({
  matches: ["https://*.vu.edu.pk/*"],
  async main() {

    await LMSProcessSync();

    // Background Alarm or Force Refresh
    browser.runtime.onMessage.addListener((message) => {
      if (message.action === "TRIGGER_LMS_FETCH") {
        console.log(
          "[Content Script] Auto-fetch triggered by background alarm.",
        );
        LMSProcessSync().catch((err) => {
          console.error("[Content Script] Error running LMSProcessSync:", err);
        });
      }
    });
  },
});
