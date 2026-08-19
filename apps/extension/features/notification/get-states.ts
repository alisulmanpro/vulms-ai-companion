const NOTIFICATION_STORAGE_KEY = "notification_store" as const;

export const getTrackedItems = async (): Promise<TrackedNotificationItem[]> => {
  try {
    const result = await browser.storage.local.get(NOTIFICATION_STORAGE_KEY);
    return (
      (result[NOTIFICATION_STORAGE_KEY] as TrackedNotificationItem[]) || []
    );
  } catch (error) {
    console.error("Failed to fetch tracked items:", error);
    return [];
  }
};

export const saveTrackedItems = async (
  items: TrackedNotificationItem[],
): Promise<void> => {
  try {
    await browser.storage.local.set({ [NOTIFICATION_STORAGE_KEY]: items });
  } catch (error) {
    console.error("Failed to save tracked items:", error);
  }
};

export const evaluateAndSyncPendingItems = async (
  freshSnapshot: LmsSnapshot,
): Promise<TrackedNotificationItem[]> => {
  const existingTracked = await getTrackedItems();
  const trackedMap = new Map(existingTracked.map((item) => [item.id, item]));
  const updatedTrackedList: TrackedNotificationItem[] = [];

  const now = Date.now();

  // Helper to sync single item state
  const processItem = (
    id: string,
    type: ItemType,
    title: string,
    subjectCode: string | undefined,
    dueDate: number,
    isCompleted: boolean,
    isOpen?: boolean,
  ) => {
    const existing = trackedMap.get(id);

    if (existing) {
      existing.isCompleted = isCompleted;
      if (isOpen !== undefined) existing.isOpen = isOpen;
      existing.dueDate = dueDate;

      updatedTrackedList.push(existing);
    } else {
      const newItem: TrackedNotificationItem = {
        id,
        type,
        title,
        subjectCode,
        dueDate,
        isOpen,
        isCompleted,
        stage: 0,
        notifyCount: 0,
        lastNotifiedAt: null,
        cooldownUntil: null,
      };
      updatedTrackedList.push(newItem);
    }
  };

  // 1. Evaluate Quizzes (Check isOpen & Attempted)
  if (freshSnapshot.quizzes) {
    Object.entries(freshSnapshot.quizzes).forEach(([subject, quizList]) => {
      quizList.forEach((q) => {
        const id = `quiz_${subject}_${q.title.replace(/\s+/g, "_")}`;
        const isAttempted =
          q.status?.toLowerCase().includes("attempted") ?? false;
        processItem(
          id,
          "quiz",
          q.title,
          subject,
          new Date(q.dueDate).getTime(),
          isAttempted,
          q.isOpen,
        );
      });
    });
  }

  // 2. Evaluate GDB (Check isOpen & Submitted)
  if (freshSnapshot.gdb) {
    Object.entries(freshSnapshot.gdb).forEach(([subject, gdbList]) => {
      gdbList.forEach((g) => {
        const id = `gdb_${subject}_${g.question.replace(/\s+/g, "_")}`;
        const isSubmitted =
          g.status?.toLowerCase().includes("submitted") ?? false;
        processItem(
          id,
          "gdb",
          g.question,
          subject,
          new Date(g.dueDate).getTime(),
          isSubmitted,
          g.isOpen,
        );
      });
    });
  }

  // 3. Evaluate Assignments (No isOpen concept)
  if (freshSnapshot.assignments) {
    Object.entries(freshSnapshot.assignments).forEach(
      ([subject, assignList]) => {
        assignList.forEach((a) => {
          const id = `assignment_${subject}_${a.title.replace(/\s+/g, "_")}`;
          const isSubmitted =
            a.status?.toLowerCase().includes("submitted") ?? false;
          processItem(
            id,
            "assignment",
            a.title,
            subject,
            new Date(a.dueDate).getTime(),
            isSubmitted,
          );
        });
      },
    );
  }

  // 4. Evaluate Fee Accounts (Check Paid / Unpaid)
  if (freshSnapshot.accounts?.challansList) {
    freshSnapshot.accounts.challansList.forEach((c) => {
      const id = `fee_${c.challanNo}`;
      const isPaid = c.paidDate !== "";
      processItem(
        id,
        "fee",
        `Fee Challan #${c.challanNo}`,
        undefined,
        new Date(c.dueDate).getTime(),
        isPaid,
      );
    });
  }

  // Sirf woh items filter karein jo PENDING hain aur notify karne ke kabil hain
  const pendingItems = updatedTrackedList.filter((item) => {
    if (item.isCompleted) return false; // Already done
    if ((item.type === "quiz" || item.type === "gdb") && item.isOpen === false)
      return false; // Not open yet
    return item.dueDate > now; // Not expired
  });

  if (pendingItems.length === 0) {
    // Agar koi b pending data nahi ha to local storage se remove kar dein
    try {
      await browser.storage.local.remove(NOTIFICATION_STORAGE_KEY);
    } catch (error) {
      console.error("Failed to remove tracked items:", error);
    }
  } else {
    // Storage mein updated state save karein
    await saveTrackedItems(updatedTrackedList);
  }

  return pendingItems;
};
