import lms_fetcher from "@/libs/lms-fetcher";

export default defineContentScript({
  matches: ['https://*.vu.edu.pk/*'],
  async main() {
    console.log('Hello content.');

    // Page load par initial fetch
    await lms_fetcher();

    // Background Alarm ya Force Refresh se trigger hone par fetch
    browser.runtime.onMessage.addListener(async (message) => {
      if (message.action === 'TRIGGER_LMS_FETCH') {
        console.log('[Content Script] Auto-fetch triggered by background alarm.');
        await lms_fetcher();
      }
    });
  },
});