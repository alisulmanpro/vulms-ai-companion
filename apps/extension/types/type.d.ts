declare global {

    interface Assignment {
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
        srNo: string;
        title: string;
        startDate: string;
        dueDate: string;
        totalMarks: string;
        isOpen: boolean
        status: string;
        score: string;
    }

    interface GDB {
        srNo: string;
        question: string;
        startDate: string;
        dueDate: string;
        totalMarks: string;
        isOpen: boolean
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

    type CourseAssignments = Record<string, Assignment[]>;
    type CourseQuiz = Record<string, Quiz[]>;
    type CourseGDB = Record<string, GDB[]>;
}

export { }