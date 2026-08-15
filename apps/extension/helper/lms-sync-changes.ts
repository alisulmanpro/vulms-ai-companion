import { detectArrayChanges } from "./diffDetector";

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
        changes.forEach(event => events.push({ ...event, courseCode }));
    }
    return events;
};

// Matches Quizzes by 'title' (e.g. "Quiz No 1") per course
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
        changes.forEach(event => events.push({ ...event, courseCode }));
    }
    return events;
};

// Matches GDBs by 'question' per course
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
        changes.forEach(event => events.push({ ...event, courseCode }));
    }
    return events;
};

// Matches Fees by 'challanNo'
export const diffAccounts = (
    oldData: AccountSummary | null,
    newData: AccountSummary | null
): DataChangeEvent<Challan>[] => {
    const oldList = oldData?.challansList || [];
    const newList = newData?.challansList || [];
    return detectArrayChanges(oldList, newList, 'challanNo', 'fee');
};
