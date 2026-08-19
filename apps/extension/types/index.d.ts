declare global {
    interface Assignment {
        id: string;
        assignmentId?: string;
        srNo: string;
        title: string;
        dueDate: string;
        totalMarks: string;
        status: string;
        score: string;
        downloadUrl: string;
        commentsUrl: string;
    }

    interface HomeFetchResult {
        viewState: string;
        vsGenerator: string;
        hfCourseCode: string;
        courses: CourseInfo[];
    }

    interface CourseInfo {
        courseCode: string;
        ctlId: string;
        index: number;
    }

    interface PostPayloadParams {
        viewState: string;
        vsGenerator: string;
        hfCourseCode: string;
        ctlId: string;
    }

    interface Quiz {
        id: string;
        quizId?: string;
        srNo: string;
        title: string;
        startDate: string;
        dueDate: string;
        totalMarks: string;
        isOpen: boolean;
        status: string;
        score: string;
    }

    interface GDB {
        id: string;
        gdbId?: string;
        srNo: string;
        question: string;
        startDate: string;
        dueDate: string;
        totalMarks: string;
        isOpen: boolean;
        status: string;
        score: string;
        viewURL: string;
    }

    interface AccountSummary {
        totalFees: number;
        challansList: Challan[];
        pageUrl: string;
    }

    interface Challan {
        challanNo: string;
        payableFee: number;
        originalPayableFee: number;
        dueDate: string;
        paidDate: string;
        lateFeeApplied: boolean;
        printUrl: string;
    }

    interface DataChangeEvent<T = any> {
        eventType: "ADDED" | "UPDATED" | "REMOVED";
        category: "quiz" | "assignment" | "gdb" | "activity" | "fee";
        courseCode?: string;
        data: T;
        timestamp: number;
    }

    interface SyncPayload {
        userId?: string;
        events: DataChangeEvent[];
        syncedAt: number;
    }

    type CourseAssignments = Record<string, Assignment[]>;
    type CourseQuiz = Record<string, Quiz[]>;
    type CourseGDB = Record<string, GDB[]>;

    // ─── Observer Engine Types ────────────────────────────────────────────────

    /** Unified LMS snapshot stored at `local:lms_data`. */
    interface LmsSnapshot {
        assignments: CourseAssignments;
        quizzes: CourseQuiz;
        gdb: CourseGDB;
        accounts: AccountSummary | null;
        fetchedAt: number;
    }

    /** A single detected difference emitted by the Observer Engine. */
    interface ObservedDiff<T = object> {
        category: "quiz" | "assignment" | "gdb" | "fee";
        eventType: "ADDED" | "UPDATED" | "REMOVED";
        courseCode?: string;
        details: T;
    }

    /** Returned when storage was empty — baseline has been set for the first time. */
    interface ObserverInitialized {
        status: "INITIALIZED";
        message: string;
        differences: [];
    }

    /** Returned when fresh data matches the stored baseline exactly. */
    interface ObserverNoDifference {
        status: "NO_DIFFERENCE";
        message: string;
        differences: [];
    }

    /** Returned when at least one change is detected. */
    interface ObserverChangesDetected {
        status: "CHANGES_DETECTED";
        timestamp: number;
        differences: ObservedDiff<object>[];
    }

    /** Discriminated union of all possible Observer Engine return values. */
    type ObserverResult =
        | ObserverInitialized
        | ObserverNoDifference
        | ObserverChangesDetected;

    type ItemType = "quiz" | "assignment" | "gdb" | "fee";

    interface TrackedNotificationItem {
        id: string;
        type: ItemType;
        title: string;
        subjectCode?: string;
        dueDate: number;

        // Specific Status
        isOpen?: boolean;
        isCompleted: boolean;

        // Notification Tracker State
        stage: number;
        notifyCount: number;
        lastNotifiedAt: number | null;
        cooldownUntil: number | null;
    }

    interface ServerNotificationPayload {
        itemId: string;
        type: ItemType;
        title: string;
        subjectCode?: string;
        urgency: 'INFO' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
        stage: number;
        message: string;
        hoursLeft: number;
        dueDate: number;
        dispatchedAt: number;
    }
}

export { };
