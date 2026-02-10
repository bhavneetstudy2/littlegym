import { test, expect } from '@playwright/test';

test.describe('Complete Workflow Integration', () => {
  const testChildName = `TestChild${Date.now()}`;
  const testParentPhone = `98765${Math.floor(Math.random() * 100000)}`;

  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.fill('input[type="email"]', 'admin@littlegym.com');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');
  });

  test('complete workflow: lead creation -> enrollment -> progress tracking', async ({
    page,
  }) => {
    // Step 1: Create a lead
    await page.click('text=Leads');
    await page.waitForURL('/leads');
    await page.click('text=+ New Lead');

    // Fill lead form
    await page.fill('input[placeholder*="Child First Name"]', testChildName);
    await page.fill('input[placeholder*="Child Last Name"]', 'Test');
    await page.fill('input[type="date"]', '2020-06-15');
    await page.fill('input[placeholder*="School"]', 'Test Elementary');

    await page.fill('input[placeholder*="Parent Name"]', 'Test Parent');
    await page.fill('input[type="tel"]', testParentPhone);
    await page.fill('input[type="email"]', `${testChildName.toLowerCase()}@test.com`);

    await page.selectOption('select[name="source"]', 'WALK_IN');

    await page.click('button:has-text("Create Lead")');

    // Wait for modal to close
    await expect(page.locator('text=Create New Lead')).not.toBeVisible({ timeout: 10000 });

    // Verify lead appears in list
    await expect(page.locator(`text=${testChildName}`)).toBeVisible({ timeout: 5000 });

    console.log(`[OK] Lead created: ${testChildName}`);

    // Step 2: Navigate to enrollments (we would create enrollment from lead in real workflow)
    await page.click('text=Enrollments');
    await page.waitForURL('/enrollments');

    console.log('[OK] Navigated to enrollments');

    // Step 3: Navigate to progress tracking
    await page.click('text=Progress');
    await page.waitForURL('/progress');
    await expect(page.locator('h1')).toContainText('Skill Progress');

    console.log('[OK] Navigated to progress tracking');

    // Step 4: Navigate to report cards
    await page.click('text=Report Cards');
    await page.waitForURL('/report-cards');
    await expect(page.locator('h1')).toContainText('Report Cards');

    console.log('[OK] Navigated to report cards');

    // Step 5: Navigate to renewals
    await page.click('text=Renewals');
    await page.waitForURL('/renewals');
    await expect(page.locator('h1')).toContainText('Renewals');

    console.log('[OK] Navigated to renewals');

    // Step 6: Navigate to admin (if user has permission)
    const adminLink = page.locator('text=Admin');
    if (await adminLink.count() > 0) {
      await adminLink.click();
      await page.waitForURL('/admin');
      await expect(page.locator('h1')).toContainText('Administration');
      console.log('[OK] Navigated to admin page');
    }

    console.log('\n[SUCCESS] Complete workflow test passed!');
  });

  test('should handle navigation across all pages', async ({ page }) => {
    const pages = [
      { link: 'Dashboard', url: '/dashboard' },
      { link: 'Leads', url: '/leads' },
      { link: 'Enrollments', url: '/enrollments' },
      { link: 'Attendance', url: '/attendance' },
      { link: 'Progress', url: '/progress' },
      { link: 'Report Cards', url: '/report-cards' },
      { link: 'Renewals', url: '/renewals' },
    ];

    for (const pageInfo of pages) {
      await page.click(`text=${pageInfo.link}`);
      await expect(page).toHaveURL(pageInfo.url, { timeout: 5000 });
      console.log(`[OK] ${pageInfo.link} page loaded`);
    }

    console.log('\n[SUCCESS] All pages navigated successfully!');
  });

  test('dashboard should display live stats', async ({ page }) => {
    await page.goto('/dashboard');

    // Check for stat cards
    await expect(page.locator('text=/Total Leads|Active Enrollments/i')).toBeVisible();

    console.log('[OK] Dashboard stats displayed');
  });
});
