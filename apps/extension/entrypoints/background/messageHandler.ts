export const setupMessageListeners = () => {
    browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
        if (message.type === "FORCE_REFRESH_LMS") {
            console.log("[Background Messaging] Force refresh requested.");
            // Execute fetcher logic
            sendResponse({ status: "started" });
        }
        return true; // Async response support
    });
};