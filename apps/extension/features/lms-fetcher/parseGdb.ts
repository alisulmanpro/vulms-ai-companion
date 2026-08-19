import { BASE_URL } from "@/constants/baseURLs";
import { fetchHomePage, parseHtml } from "./parseAssignments";

const ENDPOINTS = {
  home: `${BASE_URL}/Home.aspx`,
  listView: `${BASE_URL}/GDB/Default.aspx`,
} as const;

const parseGDBTable = (doc: Document, course: CourseInfo): GDB[] => {
  const gdb: GDB[] = [];

  const panels = [
    ...doc.querySelectorAll<HTMLElement>(
      'div[id^="MainContent_gvTileRepeaterGDB_pnl_"]',
    ),
  ];

  for (const panel of panels) {
    const getText = (selector: string) =>
      panel.querySelector(selector)?.textContent?.trim() ?? "";

    const question = getText('span[id*="lblTitle_"]');

    const dueDate = getText('span[id*="Label3_"]');

    const startDate = getText('span[id*="Label4_"]');

    const totalMarks = getText('span[id*="Label9_"]');

    const status =
      getText('span[id*="lblSubmissionStatus_"] > span:first-child') ||
      "Not Submitted";

    const score = getText('span[id*="lblMarksObtained_"]');

    const isOpen = getText('span[id*="lblStatus_"]').toLowerCase() === "open";

    const viewURL =
      panel
        .querySelector<HTMLAnchorElement>('a[id*="lbtnView_"]')
        ?.getAttribute("href") ?? "";

    const srNo =
      panel
        .querySelector(
          ".hideinMobileView.col-xs-9.col-sm-9.col-md-1.rightBorder",
        )
        ?.textContent?.trim() ?? "";

    gdb.push({
      id: `${course.courseCode}_sr${srNo}`,
      srNo,
      question,
      startDate,
      dueDate,
      totalMarks,
      score,
      status,
      isOpen,
      viewURL,
    });
  }

  return gdb;
};

const fetchCourseGDB = async (
  course: CourseInfo,
  viewState: string,
  vsGenerator: string,
  hfCourseCode: string,
): Promise<{ gdb: GDB[]; newViewState: string; newVsGenerator: string }> => {
  const payload = new URLSearchParams({
    __VIEWSTATE: viewState,
    __VIEWSTATEGENERATOR: vsGenerator,
    __EVENTTARGET: "",
    __EVENTARGUMENT: "",
    ctl00$MainContent$hfCourseCode: hfCourseCode,
    ctl00$MainContent$hfCurSemester: "",
    ctl00$MainContent$hfLessonNumber: "",
    [`ctl00$MainContent$gvCourseList$${course.ctlId}$ibtnGDB.x`]: "6",
    [`ctl00$MainContent$gvCourseList$${course.ctlId}$ibtnGDB.y`]: "21",
  });

  // Step 1: POST to Home to set active course in ASP.NET Session
  const postRes = await fetch(ENDPOINTS.home, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: payload.toString(),
    credentials: "include",
  });

  parseHtml(await postRes.text());

  // Step 2: GET GDB list for the selected course
  const listRes = await fetch(ENDPOINTS.listView, { credentials: "include" });
  const listDoc = parseHtml(await listRes.text());

  return {
    gdb: parseGDBTable(listDoc, course),
    newViewState: viewState,
    newVsGenerator: vsGenerator,
  };
};

const parseGdb = async (): Promise<CourseGDB> => {
  const allData: CourseGDB = {};

  console.log("[GDB Scrapper] Scanning Home Page...");
  const initial = await fetchHomePage();

  let currentViewState = initial.viewState;
  let currentVsGenerator = initial.vsGenerator;

  for (const course of initial.courses) {
    console.log(
      `[GDB Scrapper] < ${course.index + 1}/${initial.courses.length} > Fetching ${course.courseCode}...`,
    );
    try {
      const { gdb, newViewState, newVsGenerator } = await fetchCourseGDB(
        course,
        currentViewState,
        currentVsGenerator,
        initial.hfCourseCode,
      );

      // Update ViewState for the next iteration
      currentViewState = newViewState;
      currentVsGenerator = newVsGenerator;

      allData[course.courseCode] = gdb;
    } catch (error) {
      console.error(`Error processing ${course.courseCode}:`, error);
      allData[course.courseCode] = [];
    }
  }

  return allData;
};

export default parseGdb;
