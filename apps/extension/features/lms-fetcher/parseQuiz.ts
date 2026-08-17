import { BASE_URL } from "@/constants/baseURLs";
import { fetchHomePage, parseHtml } from "./parseAssignments";

const ENDPOINTS = {
    home: `${BASE_URL}/Home.aspx`,
    listView: `${BASE_URL}/Quiz/QuizList.aspx`,
} as const;

const parseQuizTable = (doc: Document): Quiz[] => {
    const quizzes: Quiz[] = []

    const panels = [
        ...doc.querySelectorAll<HTMLElement>(
            'div[id^="MainContent_gvTileRepeaterQuiz_pnl_"]'
        ),
    ];

    for (const panel of panels) {
        const getText = (selector: string) =>
            panel.querySelector(selector)?.textContent?.trim() ?? "";

        const title =
            getText('span[id*="lblTitle_"]');

        const dueDate =
            getText('span[id*="lblEndDate_"]');

        const startDate =
            getText('span[id*="lblStartDate_"]');

        const totalMarks =
            getText('span[id*="lblTotalMarks_"]');

        const status =
            getText('span[id*="lblSubmitted_"] > span:first-child') || "Not Submitted";

        const score =
            getText('span[id*="lblGetMarks_"]');

        const isOpen =
            getText('span[id*="lblStatus_" i]').toLowerCase() === "open";

        const srNo =
            panel
                .querySelector(
                    '.hideinMobileView.col-xs-9.col-sm-9.col-md-1.rightBorder'
                )
                ?.textContent
                ?.trim() ?? "";

        quizzes.push({
            srNo,
            title,
            startDate,
            dueDate,
            totalMarks,
            score,
            status,
            isOpen,
        })

    }

    return quizzes;
}

const fetchCourseQuiz = async (
    course: CourseInfo,
    viewState: string,
    vsGenerator: string,
    hfCourseCode: string
): Promise<{ quizzes: Quiz[]; newViewState: string; newVsGenerator: string }> => {
    const payload = new URLSearchParams({
        '__VIEWSTATE': viewState,
        '__VIEWSTATEGENERATOR': vsGenerator,
        '__EVENTTARGET': '',
        '__EVENTARGUMENT': '',
        'ctl00$MainContent$hfCourseCode': hfCourseCode,
        'ctl00$MainContent$hfCurSemester': '',
        'ctl00$MainContent$hfLessonNumber': '',
        [`ctl00$MainContent$gvCourseList$${course.ctlId}$ibtnQuizzes.x`]: '13',
        [`ctl00$MainContent$gvCourseList$${course.ctlId}$ibtnQuizzes.y`]: '23',
    });


    // Step 1: POST to Home to set active course in ASP.NET Session
    const postRes = await fetch(ENDPOINTS.home, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: payload.toString(),
        credentials: 'include',
    });

    parseHtml(await postRes.text());

    // Step 2: Direct GET to StudentAssignmentListView.aspx (Skipped redundant Assignments.aspx)
    const listRes = await fetch(ENDPOINTS.listView, { credentials: 'include' });
    const listDoc = parseHtml(await listRes.text());

    return {
        quizzes: parseQuizTable(listDoc),
        newViewState: viewState,
        newVsGenerator: vsGenerator,
    };
}

const parseQuiz = async (): Promise<CourseQuiz> => {
    const allData: CourseQuiz = {};

    console.log('[Quiz Scrapper] Scanning Home Page...');
    const initial = await fetchHomePage();

    let currentViewState = initial.viewState;
    let currentVsGenerator = initial.vsGenerator;

    for (const course of initial.courses) {
        console.log(`[Quiz Scrapper] < ${course.index + 1}/${initial.courses.length}] > Fetching ${course.courseCode}...`);
        ``
        try {
            const { quizzes, newViewState, newVsGenerator } = await fetchCourseQuiz(
                course, currentViewState, currentVsGenerator, initial.hfCourseCode
            );

            // Update ViewState for the next iteration
            currentViewState = newViewState;
            currentVsGenerator = newVsGenerator;

            allData[course.courseCode] = quizzes;

            // Progressive Storage Update (Instant Save)
            await storage.setItem('local:quizzes', { ...allData });

        } catch (error) {
            console.error(`Error processing ${course.courseCode}:`, error);
            allData[course.courseCode] = [];
        }
    }

    return allData;
}

export default parseQuiz
