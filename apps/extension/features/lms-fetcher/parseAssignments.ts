import { BASE_URL } from "@/constants/baseURLs";

const SELECTORS = {
    viewState: '[name="__VIEWSTATE"]',
    vsGenerator: '[name="__VIEWSTATEGENERATOR"]',
    hfCourseCode: '[name="ctl00$MainContent$hfCourseCode"]',
    assignmentButtons: 'input[type="image"][id^="MainContent_gvCourseList_ibtnAssignments_"]',
} as const;

const ENDPOINTS = {
    home: `${BASE_URL}/Home.aspx`,
    listView: `${BASE_URL}/Assignments/StudentAssignmentListView.aspx`,
} as const;

const parseHtml = (html: string): Document => new DOMParser().parseFromString(html, 'text/html');

const extractViewStateTokens = (doc: Document) => ({
    viewState: doc.querySelector<HTMLInputElement>(SELECTORS.viewState)?.value ?? '',
    vsGenerator: doc.querySelector<HTMLInputElement>(SELECTORS.vsGenerator)?.value ?? '',
});

const extractCourseList = (doc: Document): CourseInfo[] => {
    const courses: CourseInfo[] = [];
    const buttons = doc.querySelectorAll<HTMLInputElement>(SELECTORS.assignmentButtons);

    for (const btn of buttons) {
        const idSuffix = btn.id.split('_').pop();
        const index = parseInt(idSuffix ?? '', 10);
        if (isNaN(index)) continue;

        const ctlId = btn.name.split('$')[3];
        if (!ctlId) continue;

        const trackingSpan = doc.querySelector<HTMLSpanElement>(`#MainContent_gvCourseList_lblTracking_${index}`);
        const titleText = (trackingSpan?.closest('h3')?.firstChild as Text | null)?.textContent?.trim() ?? '';
        const courseCode = titleText.split('-')[0]?.trim();

        if (courseCode) {
            courses.push({ courseCode, ctlId, index });
        }
    }
    return courses;
};

const fetchHomePage = async (): Promise<HomeFetchResult> => {
    const res = await fetch(ENDPOINTS.home, { credentials: 'include' });
    if (!res.ok) throw new Error(`[Home Scrapper] Request failed: ${res.status}`);

    const doc = parseHtml(await res.text());
    const { viewState, vsGenerator } = extractViewStateTokens(doc);
    const hfCourseCode = doc.querySelector<HTMLInputElement>(SELECTORS.hfCourseCode)?.value ?? '';

    if (!viewState) throw new Error('[Assignments Scrapper] __VIEWSTATE not found — session expired');

    const courses = extractCourseList(doc);
    if (courses.length === 0) throw new Error('[Assignments Scrapper] No courses found');

    return { viewState, vsGenerator, hfCourseCode, courses };
};

const parseAssignmentTable = (doc: Document): Assignment[] => {
    const assignments: Assignment[] = [];

    const panels = [
        ...doc.querySelectorAll<HTMLElement>(
            'div[id^="MainContent_gvTileRepeaterAssignment_pnl_"]'
        ),
    ];

    for (const panel of panels) {
        const getText = (selector: string) =>
            panel.querySelector(selector)?.textContent?.trim() ?? "";

        const title =
            getText('span[id*="Label3_"]');

        const dueDate =
            getText('span[id*="lblDueDate_"]');

        const totalMarks =
            getText('span[id*="lblTotalMarks_"]');

        const status =
            getText('span[id*="lblsubmitted_"]') || "Not Submitted";

        const score =
            getText('span[id*="lblScore_"]');

        const downloadUrl =
            panel
                .querySelector<HTMLAnchorElement>(
                    'a[id*="lbtnViewSubmittedFile_"]'
                )
                ?.getAttribute("href") ?? "";

        const commentsUrl =
            panel
                .querySelector<HTMLAnchorElement>(
                    'a[href*="InstructorComments.aspx"]'
                )
                ?.getAttribute("href") ?? "";

        const srNo =
            panel
                .querySelector(
                    '.hideinMobileView.col-xs-9.col-sm-9.col-md-1.rightBorder'
                )
                ?.textContent
                ?.trim() ?? "";

        assignments.push({
            srNo,
            title,
            dueDate,
            totalMarks,
            status,
            score,
            downloadUrl,
            commentsUrl: `${BASE_URL}/Assignments/${commentsUrl}`,
        });
    }

    return assignments;
}

const fetchCourseAssignments = async (
    course: CourseInfo,
    viewState: string,
    vsGenerator: string,
    hfCourseCode: string
): Promise<{ assignments: Assignment[]; newViewState: string; newVsGenerator: string }> => {

    const payload = new URLSearchParams({
        '__VIEWSTATE': viewState,
        '__VIEWSTATEGENERATOR': vsGenerator,
        '__EVENTTARGET': '',
        '__EVENTARGUMENT': '',
        'ctl00$MainContent$hfCourseCode': hfCourseCode,
        'ctl00$MainContent$hfCurSemester': '',
        'ctl00$MainContent$hfLessonNumber': '',
        [`ctl00$MainContent$gvCourseList$${course.ctlId}$ibtnAssignments.x`]: '17',
        [`ctl00$MainContent$gvCourseList$${course.ctlId}$ibtnAssignments.y`]: '13',
    });

    // Step 1: POST to Home to set active course in ASP.NET Session
    const postRes = await fetch(ENDPOINTS.home, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: payload.toString(),
        credentials: 'include',
    });

    const postDoc = parseHtml(await postRes.text());
    const newTokens = extractViewStateTokens(postDoc);

    // Step 2: Direct GET to StudentAssignmentListView.aspx (Skipped redundant Assignments.aspx)
    const listRes = await fetch(ENDPOINTS.listView, { credentials: 'include' });
    const listDoc = parseHtml(await listRes.text());

    return {
        assignments: parseAssignmentTable(listDoc),
        newViewState: newTokens.viewState || viewState,
        newVsGenerator: newTokens.vsGenerator || vsGenerator,
    };
};

const parseAssignments = async (): Promise<CourseAssignments> => {
    const allData: CourseAssignments = {};

    console.log('[Assignments Scrapper] Scanning Home Page...');
    const initial = await fetchHomePage();

    let currentViewState = initial.viewState;
    let currentVsGenerator = initial.vsGenerator;

    for (const course of initial.courses) {
        console.log(`[Assignments Scrapper] < ${course.index + 1}/${initial.courses.length} > Fetching ${course.courseCode}...`);

        try {
            const { assignments, newViewState, newVsGenerator } = await fetchCourseAssignments(
                course, currentViewState, currentVsGenerator, initial.hfCourseCode
            );

            // Update ViewState for the next iteration
            currentViewState = newViewState;
            currentVsGenerator = newVsGenerator;

            allData[course.courseCode] = assignments;

            // Progressive Storage Update (Instant Save)
            await storage.setItem('local:assignments', { ...allData });

        } catch (error) {
            console.error(`[Assignments Scrapper] Error processing ${course.courseCode}:`, error);
            allData[course.courseCode] = [];
        }
    }

    return allData;
};

export { fetchHomePage, extractViewStateTokens, parseHtml }
export default parseAssignments;
