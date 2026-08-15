const ALARM_NAME = "LMS_FETCHER_AUTO_RUN";

/**
 * Cooldown khatam hone ke exact waqt ke liye Alarm schedule karta hai
 */
export const scheduleNextAutoFetch = async (cooldownMinutes = 5) => {
    if (typeof browser !== 'undefined' && browser.alarms) {
        // Background context
        await browser.alarms.clear(ALARM_NAME);
        browser.alarms.create(ALARM_NAME, {
            delayInMinutes: cooldownMinutes
        });
        console.log(`[Scheduler] Alarm set for ${cooldownMinutes} minutes from now.`);
    } else if (typeof browser !== 'undefined' && browser.runtime?.sendMessage) {
        // Content script context (alarms API is not available directly)
        await browser.runtime.sendMessage({
            action: 'SCHEDULE_AUTO_FETCH',
            cooldownMinutes
        });
        console.log(`[Scheduler] Sent SCHEDULE_AUTO_FETCH message to background for ${cooldownMinutes} minutes.`);
    }
};