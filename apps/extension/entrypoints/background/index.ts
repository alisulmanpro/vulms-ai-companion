import { setupAlarmListeners } from './alarms';
import { setupMessageListeners } from './messages';

export default defineBackground(() => {
    console.log('[Background Service Worker] Initialized.');

    // Initialize modular features
    setupAlarmListeners();
    setupMessageListeners();
});
