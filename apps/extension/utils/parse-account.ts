const parse_accounts = async (): Promise<AccountSummary | null> => {
    try {
        const pageUrl = `${BASE_URL}/AccountBook/AccountBook.aspx`;

        // 1. Fetch HTML from LMS (Extension session cookies automatically sath bhejta hai)
        const response = await fetch(pageUrl, {
            method: "GET",
            headers: {
                "Accept": "text/html",
            },
        });


        if (!response.ok) {
            console.error(`Account Scraper: Request failed with status ${response.status}`);
            return null;
        }

        // 2. HTML string ko Document object mein convert karein
        const doc = parseHtml(await response.text());
        
        // 3. Validation Check on parsed document
        const hasAccountGrid = doc.querySelector('[id*="grdaccountbook"]') !== null;
        if (!hasAccountGrid) {
            console.log("Account Scraper: Account grid not found in fetched page.");
            return null;
        }
        
        const challans: Challan[] = [];
        const panels = doc.querySelectorAll('[id^="MainContent_grdaccountbook_pnl_"]');
        
        panels.forEach((pnl) => {
            const idSuffix = pnl.id.split('_').pop();
            if (!idSuffix) return;
            
            // Dates Selectors
            const paidDateEl = pnl.querySelector<HTMLElement>(`#MainContent_grdaccountbook_lblpaiddate_${idSuffix}`);
            const paidDateText = paidDateEl?.textContent?.trim() || "";

            // Parse only "UnPaid" challans
            if (paidDateText.toLowerCase() !== "unpaid") {
                return;
            }

            // Challan Number
            const challanNoEl = pnl.querySelector<HTMLElement>(`#MainContent_grdaccountbook_lbl_${idSuffix}`);
            if (!challanNoEl) return;
            const challanNo = challanNoEl.textContent.trim();

            // Original Payable Fee
            const payableAmountEl = pnl.querySelector<HTMLElement>(`#MainContent_grdaccountbook_lblPayableAmount_${idSuffix}`);
            let payableFee = parseInt(payableAmountEl?.textContent?.trim() ?? "0", 10) || 0;

            const dueDateEl = pnl.querySelector<HTMLElement>(`#MainContent_grdaccountbook_lblduedate_${idSuffix}`);
            const dueDateText = dueDateEl?.textContent?.trim() || "";

            // Unpaid Late Fee Calculation
            let extraCharges = 0;
            if (dueDateText) {
                const dueDate = new Date(dueDateText);
                const currentDate = new Date();

                if (currentDate > dueDate) {
                    payableFee += 200;
                    extraCharges = 200;
                }
            }

            // Dynamic Print URL Parsing
            let printUrl = `${BASE_URL}/AccountBook/PrintChallan.aspx?ChallanNo=${challanNo}`;
            const printBtn = pnl.querySelector<HTMLInputElement>(`#MainContent_grdaccountbook_hlPrint_${idSuffix}`);

            if (printBtn) {
                const onClickAttr = printBtn.getAttribute("onclick") || "";
                const urlMatch = onClickAttr.match(/["'](ChallanPrintPreview\.aspx\?[^"']+)["']/);

                if (urlMatch && urlMatch[1]) {
                    printUrl = `${BASE_URL}/AccountBook/${urlMatch[1]}`;
                }
            }

            challans.push({
                challanNo,
                originalPayableFee: payableFee - extraCharges,
                lateFeeApplied: extraCharges > 0,
                payableFee,
                dueDate: dueDateText,
                paidDate: paidDateText,
                printUrl
            });
        });

        const grandTotalFees = challans.reduce((sum, item) => sum + item.payableFee, 0);

        return {
            totalFees: grandTotalFees,
            challansList: challans,
            pageUrl
        };

    } catch (error) {
        console.error("Account Scraper Error:", error);
        return null;
    }
}

export default parse_accounts;