import { canRunLmsFetcher } from "@/helper/lmsFetcherGuard";
import { scheduleNextAutoFetch } from "@/helper/lmsScheduler";

export const setupAlarmListeners = () => {
    browser.alarms.onAlarm.addListener(async (alarm) => {
        if (alarm.name === "LMS_FETCHER_AUTO_RUN") {
            console.log("[Background Alarms] Cooldown ended, checking fetcher...");
            
            const canRun = await canRunLmsFetcher();
            if (!canRun) {
                console.log("[Background Alarms] Cooldown is still active. Skipping.");
                return;
            }

            // Find open LMS tabs and trigger content script
            const tabs = await browser.tabs.query({ url: "*://*.vu.edu.pk/*" });
            if (tabs.length > 0) {
                const targetTab = tabs.find(t => t.active) ?? tabs[0];
                if (targetTab?.id) {
                    console.log(`[Background Alarms] Triggering fetch on tab ID ${targetTab.id}`);
                    await browser.tabs.sendMessage(targetTab.id, { action: "TRIGGER_LMS_FETCH" });
                }
            } else {
                console.log("[Background Alarms] No open LMS tab found.");
            }
        }
    });

    browser.runtime.onMessage.addListener(async (message) => {
        if (message.action === "SCHEDULE_AUTO_FETCH") {
            await scheduleNextAutoFetch(message.cooldownMinutes);
        }
    });
};