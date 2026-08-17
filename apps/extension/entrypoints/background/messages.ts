import { sendEventsToServer } from '@/services/syncService';

export const setupMessageListeners = () => {
    browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
        if (message.type === "FORCE_REFRESH_LMS") {
            console.log("[Background Messaging] Force refresh requested.");
            // Execute fetcher logic
            sendResponse({ status: "started" });
        }
        return true; // Async response support
    });

    /**
     * OBSERVER_CHANGES — fired by the Observer Engine when at least one diff
     * is detected. Routes the structured result to the sync service for API
     * dispatch and/or local notification triggers.
     */
    browser.runtime.onMessage.addListener(async (message) => {
        if (message.action === 'OBSERVER_CHANGES') {
            const result: ObserverChangesDetected = message.payload;
            console.log(
                `[Background Messaging] Observer detected ${result.differences.length} change(s). Forwarding to sync service...`
            );

            // Map ObservedDiff → DataChangeEvent for the existing sync service shape
            const events: DataChangeEvent[] = result.differences.map((diff) => ({
                eventType: diff.eventType,
                category: diff.category,
                courseCode: diff.courseCode,
                data: diff.details,
                timestamp: result.timestamp,
            }));

            await sendEventsToServer(events);
        }
    });
};
