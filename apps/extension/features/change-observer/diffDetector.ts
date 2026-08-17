export const detectArrayChanges = <T extends Record<string, any>>(
    oldList: T[] = [],
    newList: T[] = [],
    keyField: keyof T,
    category: DataChangeEvent['category']
): DataChangeEvent<T>[] => {
    const events: DataChangeEvent<T>[] = [];
    const oldMap = new Map(oldList.map((item) => [item[keyField], item]));
    const newKeys = new Set(newList.map((item) => item[keyField]));

    // Detect ADDED and UPDATED
    newList.forEach((newItem) => {
        const id = newItem[keyField];
        const oldItem = oldMap.get(id);

        if (!oldItem) {
            events.push({
                eventType: 'ADDED',
                category,
                data: newItem,
                timestamp: Date.now(),
            });
        } else if (JSON.stringify(oldItem) !== JSON.stringify(newItem)) {
            events.push({
                eventType: 'UPDATED',
                category,
                data: newItem,
                timestamp: Date.now(),
            });
        }
    });

    // Detect REMOVED
    oldList.forEach((oldItem) => {
        const id = oldItem[keyField];
        if (!newKeys.has(id)) {
            events.push({
                eventType: 'REMOVED',
                category,
                data: oldItem,
                timestamp: Date.now(),
            });
        }
    });

    return events;
};

export const diffAssignments = (
    oldData: CourseAssignments = {},
    newData: CourseAssignments = {}
): DataChangeEvent<Assignment>[] => {
    const events: DataChangeEvent<Assignment>[] = [];
    const allCourses = new Set([...Object.keys(oldData), ...Object.keys(newData)]);

    for (const courseCode of allCourses) {
        const oldList = oldData[courseCode] || [];
        const newList = newData[courseCode] || [];

        const changes = detectArrayChanges(oldList, newList, 'title', 'assignment');
        changes.forEach(event => {
            events.push({
                ...event,
                courseCode
            });
        });
    }

    return events;
};

export const diffQuizzes = (
    oldData: CourseQuiz = {},
    newData: CourseQuiz = {}
): DataChangeEvent<Quiz>[] => {
    const events: DataChangeEvent<Quiz>[] = [];
    const allCourses = new Set([...Object.keys(oldData), ...Object.keys(newData)]);

    for (const courseCode of allCourses) {
        const oldList = oldData[courseCode] || [];
        const newList = newData[courseCode] || [];

        const changes = detectArrayChanges(oldList, newList, 'title', 'quiz');
        changes.forEach(event => {
            events.push({
                ...event,
                courseCode
            });
        });
    }

    return events;
};

export const diffGdb = (
    oldData: CourseGDB = {},
    newData: CourseGDB = {}
): DataChangeEvent<GDB>[] => {
    const events: DataChangeEvent<GDB>[] = [];
    const allCourses = new Set([...Object.keys(oldData), ...Object.keys(newData)]);

    for (const courseCode of allCourses) {
        const oldList = oldData[courseCode] || [];
        const newList = newData[courseCode] || [];

        const changes = detectArrayChanges(oldList, newList, 'question', 'gdb');
        changes.forEach(event => {
            events.push({
                ...event,
                courseCode
            });
        });
    }

    return events;
};

export const diffAccounts = (
    oldData: AccountSummary | null,
    newData: AccountSummary | null
): DataChangeEvent<Challan>[] => {
    const oldList = oldData?.challansList || [];
    const newList = newData?.challansList || [];

    return detectArrayChanges(oldList, newList, 'challanNo', 'fee');
};

export const processSyncData = async (
    category: DataChangeEvent['category'],
    newData: any
) => {
    let oldData: any = null;
    let changes: DataChangeEvent[] = [];

    if (category === 'assignment') {
        oldData = await storage.getItem<CourseAssignments>('local:assignments_synced') || {};
        changes = diffAssignments(oldData, newData);
        await storage.setItem('local:assignments_synced', newData);
        await storage.setItem('local:assignments', newData);
    } else if (category === 'quiz') {
        oldData = await storage.getItem<CourseQuiz>('local:quizzes_synced') || {};
        changes = diffQuizzes(oldData, newData);
        await storage.setItem('local:quizzes_synced', newData);
        await storage.setItem('local:quizzes', newData);
    } else if (category === 'gdb') {
        oldData = await storage.getItem<CourseGDB>('local:gdb_synced') || {};
        changes = diffGdb(oldData, newData);
        await storage.setItem('local:gdb_synced', newData);
        await storage.setItem('local:gdb', newData);
    } else if (category === 'fee') {
        oldData = await storage.getItem<AccountSummary>('local:accounts_synced') || null;
        changes = diffAccounts(oldData, newData);
        await storage.setItem('local:accounts_synced', newData);
        await storage.setItem('local:accounts', newData);
    }

    if (changes.length > 0) {
        console.log(`[Diff Engine] Detected ${changes.length} changes for category "${category}":`);
        changes.forEach((event) => {
            const courseStr = event.courseCode ? `[${event.courseCode}] ` : '';
            const details = event.category === 'fee' 
                ? `Challan #${event.data.challanNo} (Payable: ${event.data.payableFee})`
                : event.category === 'gdb'
                ? `GDB: "${event.data.question}"`
                : `Item: "${event.data.title}"`;
            console.log(` -> ${event.eventType}: ${courseStr}${details}`);
        });

        // Save events to storage
        const existingEvents = await storage.getItem<DataChangeEvent[]>('local:change_events') || [];
        const updatedEvents = [...existingEvents, ...changes];
        await storage.setItem('local:change_events', updatedEvents);
    } else {
        console.log(`[Diff Engine] No changes detected for category "${category}".`);
    }
};
