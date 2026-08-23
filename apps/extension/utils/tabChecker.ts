export async function isLmsTabActive(): Promise<boolean> {
  try {
    const activeTabs = await browser.tabs.query({
      url: '*://vulms.vu.edu.pk/*',
      active: true,
      lastFocusedWindow: true,
    });

    return activeTabs.length > 0;
  } catch (error) {
    console.error('[Tab Checker] Error checking active LMS tabs:', error);
    return false;
  }
}
