import { isLmsTabActive } from "@/utils/tabChecker";
import { observeLmsData } from "@/features/change-observer/observerEngine";
import { evaluateAndSyncPendingItems } from "@/features/notification/get-states";
import processAndDispatchNotifications from "@/services/notificationEngine";

export const observerEngine = () => {
    browser.runtime.onMessage.addListener(async (request, sender) => {
        if (request.type === "OBSERVE_LMS_DATA") {
            try {
                // Step 1: Baseline Storage Comparison
                const result = await observeLmsData(request.payload);
                console.log("[Observer Engine] Observed LMS Data:", result);

                // Step 2: Safe UI Dispatch (Popup active na hone par error consume ho jayega)
                if (result.status === "CHANGES_DETECTED") {
                    browser.runtime
                        .sendMessage({
                            action: "OBSERVER_CHANGES",
                            payload: result,
                        })
                        .catch((error) => {
                            // Popup closed rehta hai to error ignore kar dein
                            console.warn(
                                "[Observer Engine] Popup closed, ignoring error:",
                                error,
                            );
                        });
                }

                // Step 3: Notification State Evaluator & Sync
                console.log(
                    "[Notification Engine] Processing snapshot & updating tracking states...",
                );

                // 1. Snapshot processing logic
                const pendingItems = await evaluateAndSyncPendingItems(request.payload);
                // 2. Dispatch Engine Execution
                const isUserOnLms = await isLmsTabActive();
                if (isUserOnLms) {
                    console.log("[Observer Engine] LMS is active.");
                } else {
                    if (pendingItems.length > 0) {
                        const serverPayloads = await processAndDispatchNotifications();
                        console.log(`[Observer Engine] Processed ${serverPayloads.length} notification payload(s).`);
                    }
                }

                // Step 4: Return response cleanly
                return {
                    result,
                    pendingItemsCount: pendingItems.length,
                };
            } catch (err) {
                console.error("[Observer Engine] Error observing LMS data:", err);
                return { result: null, error: String(err) };
            }
        }
    });
};
