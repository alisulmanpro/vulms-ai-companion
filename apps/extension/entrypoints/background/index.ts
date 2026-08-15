import { setupAlarmListeners } from './alarm';
import { setupLmsSync } from './lmsSync';
import { setupMessageListeners } from './messageHandler';

export default defineBackground(() => {
    console.log('[Background Service Worker] Initialized.');

    // Initialize modular features
    setupLmsSync();
    setupAlarmListeners();
    setupMessageListeners();
});