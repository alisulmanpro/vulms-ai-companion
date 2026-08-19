import { getTrackedItems, saveTrackedItems } from "@/features/notification/get-states";

export default async function processAndDispatchNotifications(): Promise<ServerNotificationPayload[]> {
    const items = await getTrackedItems();
    const now = Date.now();
    const HOUR_MS = 60 * 60 * 1000;

    const serverPayloads: ServerNotificationPayload[] = [];
    let storageNeedsUpdate = false;

    for (const item of items) {
        // 1. Completion & Expiry Guards
        if (item.isCompleted) continue;
        if (item.dueDate <= now) continue;

        // 2. Active Cooldown Guard (Zero Spam Check)
        if (item.cooldownUntil && now < item.cooldownUntil) {
            console.log(`[Notification Engine] Muted: ${item.id} (Cooldown active until ${new Date(item.cooldownUntil).toLocaleString()})`);
            continue;
        }

        const hoursLeft = (item.dueDate - now) / HOUR_MS;
        let newStage = item.stage;
        let urgency: 'INFO' | 'MEDIUM' | 'HIGH' | 'CRITICAL' = 'INFO';
        let message = '';
        let nextCooldownTimestamp: number | null = null;

        // 3. Stage Escalation & Exact Threshold Cooldown Logic
        if (hoursLeft <= 1 && item.stage < 3) {
            // Stage 3: Emergency (< 1 hour left)
            newStage = 3;
            urgency = 'CRITICAL';
            message = `🚨 CRITICAL: Only ${Math.max(1, Math.round(hoursLeft * 60))} minutes remaining!`;
            nextCooldownTimestamp = item.dueDate; // Lock until expiry
        } else if (hoursLeft <= 8 && item.stage < 2) {
            // Stage 2: High Urgency (< 8 hours left)
            newStage = 2;
            urgency = 'HIGH';
            message = `⚠️ URGENT: Less than ${Math.ceil(hoursLeft)} hours left to complete.`;
            nextCooldownTimestamp = item.dueDate - (1 * HOUR_MS); // Next wake up at 1h threshold
        } else if (hoursLeft <= 28 && item.stage < 1) {
            // Stage 1: Routine Reminder (< 28 hours left)
            newStage = 1;
            urgency = 'MEDIUM';
            message = `📌 REMINDER: Deadline in approx ${Math.ceil(hoursLeft)} hours.`;
            nextCooldownTimestamp = item.dueDate - (8 * HOUR_MS); // Next wake up at 8h threshold
        } else if (item.stage === 0 && item.notifyCount === 0) {
            // Stage 0: Brand New Discovery Alert
            newStage = 1;
            urgency = 'INFO';
            message = `📢 NEW ITEM: New ${item.type} released on VULMS.`;

            // Target next threshold based on current hours remaining
            if (hoursLeft > 28) {
                nextCooldownTimestamp = item.dueDate - (28 * HOUR_MS);
            } else if (hoursLeft > 8) {
                nextCooldownTimestamp = item.dueDate - (8 * HOUR_MS);
            } else {
                nextCooldownTimestamp = item.dueDate - (1 * HOUR_MS);
            }
        }

        // 4. Construct Server Payload & Lock Cooldown
        if (message && nextCooldownTimestamp !== null) {
            const payload: ServerNotificationPayload = {
                itemId: item.id,
                type: item.type,
                title: item.title,
                subjectCode: item.subjectCode,
                urgency,
                stage: newStage,
                message,
                hoursLeft: Number(hoursLeft.toFixed(2)),
                dueDate: item.dueDate,
                dispatchedAt: now,
            };

            serverPayloads.push(payload);

            // State Update
            item.stage = newStage;
            item.notifyCount += 1;
            item.lastNotifiedAt = now;
            item.cooldownUntil = nextCooldownTimestamp;
            storageNeedsUpdate = true;
        }
    }

    // 5. Commit Updated Metadata to Storage
    if (storageNeedsUpdate) {
        await saveTrackedItems(items);
    }

    // 6. Simulate Server Dispatch
    if (serverPayloads.length > 0) {
        console.log('[Notification Engine] 🚀 Dispatching Payload to Server:', serverPayloads);
    } else {
        console.log('[Notification Engine] 🔕 No notifications ready to dispatch.');
    }

    return serverPayloads;
}