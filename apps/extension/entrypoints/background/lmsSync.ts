import { processSyncData } from '@/helper/diffDetector';

export const setupLmsSync = () => {
    browser.runtime.onMessage.addListener(async (message) => {
        if (message.action === 'SYNC_ASSIGNMENTS') {
            console.log('[Assignments] Data received in background:', message.payload);
            await processSyncData('assignment', message.payload);
        }
        if (message.action === 'SYNC_QUIZZES') {
            console.log('[Quizzes] Data received in background:', message.payload);
            await processSyncData('quiz', message.payload);
        }

        if (message.action === 'SYNC_GDB') {
            console.log('[GDB] Data received in background:', message.payload);
            await processSyncData('gdb', message.payload);
        }

        if (message.action === 'SYNC_ACCOUNTS') {
            console.log('[Accounts] Data received in background:', message.payload);
            await processSyncData('fee', message.payload);
        }
    });
}