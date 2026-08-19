import { sendEventsToServer } from "@/services/syncService";

export const setupMessageListeners = () => {
  browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === "FORCE_REFRESH_LMS") {
      console.log("[Background Messaging] Force refresh requested.");
      // Execute fetcher logic
      sendResponse({ status: "started" });
      return true; // Return true ONLY if we are handling it
    }
  });

  /**
   * OBSERVER_CHANGES — fired by the Observer Engine when at least one diff
   * is detected. Routes the structured result to the sync service for API
   * dispatch and/or local notification triggers.
   */
  browser.runtime.onMessage.addListener((message) => {
    if (message.action === "OBSERVER_CHANGES") {
      const result: ObserverChangesDetected = message.payload;
      console.log(
        `[Background Messaging] Observer detected ${result.differences.length} change(s). Forwarding to sync service...`,
      );

      const events: DataChangeEvent[] = result.differences.map((diff) => ({
        eventType: diff.eventType as "ADDED" | "UPDATED" | "REMOVED",
        category: diff.category,
        courseCode: diff.courseCode,
        data: diff.details,
        timestamp: result.timestamp,
      }));

      sendEventsToServer(events).catch((err) => {
        console.error(
          "[Background Messaging] Failed to send events to server:",
          err,
        );
      });
    }
  });
};
