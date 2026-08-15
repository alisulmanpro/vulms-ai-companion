export const setupLmsSync = () => {
    browser.runtime.onMessage.addListener(async (message) => {
        if (message.action === 'SYNC_ASSIGNMENTS') {
            console.log('[Assignments] Data received in background:', message.payload);
            await storage.setItem('local:assignments', message.payload);
        }
        if (message.action === 'SYNC_QUIZZES') {
            console.log('[Quizzes] Data received in background:', message.payload);
            await storage.setItem('local:quizzes', message.payload);
        }

        if (message.action === 'SYNC_GDB') {
            console.log('[GDB] Data received in background:', message.payload);
            await storage.setItem('local:gdb', message.payload);
        }

        if (message.action === 'SYNC_ACCOUNTS') {
            console.log('[Accounts] Data received in background:', message.payload);
            await storage.setItem('local:accounts', message.payload);
        }
    });
}