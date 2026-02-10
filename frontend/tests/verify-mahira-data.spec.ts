import { test, expect } from '@playwright/test';

test.describe('Verify Mahira Data Import', () => {
  test('should login and view Mahira student profile', async ({ page }) => {
    // Login
    await page.goto('http://localhost:3000/login');
    await page.fill('input[name="email"]', 'admin@chandigarh.thelittlegym.in');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');

    // Wait for dashboard
    await page.waitForURL('**/dashboard');

    // Navigate to students page
    await page.goto('http://localhost:3000/students');

    // Wait for page to load
    await page.waitForSelector('text=Enrolled Students', { timeout: 10000 });

    // Search for Mahira
    const searchBox = page.locator('input[placeholder*="Search"]').first();
    await searchBox.fill('Mahira');
    await page.waitForTimeout(500);

    // Click on Mahira's row to open profile modal
    await page.click('text=Mahira');

    // Wait for modal to open
    await page.waitForSelector('text=Student Profile', { timeout: 5000 });

    // Verify Overview tab data
    await expect(page.locator('text=TLGC0002')).toBeVisible();
    await expect(page.locator('text=Good Friends')).toBeVisible();

    // Check stats cards
    const pageContent = await page.textContent('body');
    console.log('\\nMahira Profile Data:');
    console.log('  Enquiry ID visible:', pageContent?.includes('TLGC0002'));
    console.log('  Batch visible:', pageContent?.includes('Good Friends'));

    // Click Attendance tab
    await page.click('text=Attendance');
    await page.waitForTimeout(1000);

    // Check if attendance records are visible
    const attendanceText = await page.textContent('body');
    console.log('  Attendance records visible:', attendanceText?.includes('Apr') || attendanceText?.includes('April'));

    // Take screenshot
    await page.screenshot({ path: 'mahira-profile.png', fullPage: true });
    console.log('\\n✅ Screenshot saved as mahira-profile.png');
  });

  test('should display Mahira in students list', async ({ page }) => {
    // Login
    await page.goto('http://localhost:3000/login');
    await page.fill('input[name="email"]', 'admin@chandigarh.thelittlegym.in');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');

    // Wait for dashboard
    await page.waitForURL('**/dashboard');

    // Navigate to students page
    await page.goto('http://localhost:3000/students');

    // Wait for students to load
    await page.waitForSelector('text=Enrolled Students', { timeout: 10000 });
    await page.waitForTimeout(2000);

    // Search for Mahira
    const searchBox = page.locator('input[placeholder*="Search"]').first();
    await searchBox.fill('Mahira');
    await page.waitForTimeout(500);

    // Check if Mahira appears in the list
    const mahiraVisible = await page.isVisible('text=Mahira');
    console.log('\\nMahira in students list:', mahiraVisible);

    // Get all text on page
    const pageText = await page.textContent('body');

    // Check for expected data
    console.log('\\nData visibility checks:');
    console.log('  Student name "Mahira":', pageText?.includes('Mahira'));
    console.log('  Batch "Good Friends":', pageText?.includes('Good Friends'));
    console.log('  Batch "Grade School":', pageText?.includes('Grade School'));

    // Take screenshot
    await page.screenshot({ path: 'students-list.png', fullPage: true });
    console.log('\\n✅ Screenshot saved as students-list.png');
  });
});
