import { test, expect } from '@playwright/test';

test.describe('Enrollment Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.fill('input[type="email"]', 'admin@littlegym.com');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');
  });

  test('should navigate to enrollments page', async ({ page }) => {
    await page.click('text=Enrollments');
    await expect(page).toHaveURL('/enrollments');
    await expect(page.locator('h1')).toContainText('Enrollments');
  });

  test('should display batch overview', async ({ page }) => {
    await page.goto('/enrollments');

    // Should show batches section
    await expect(page.locator('text=Batches Overview')).toBeVisible();
  });

  test('should display active enrollments', async ({ page }) => {
    await page.goto('/enrollments');

    // Should show enrollments table
    await expect(page.locator('text=/Student Name|Plan Type/i')).toBeVisible();
  });

  test('should filter enrollments by status', async ({ page }) => {
    await page.goto('/enrollments');

    // Select status filter if available
    const statusSelect = page.locator('select');
    if (await statusSelect.count() > 0) {
      await statusSelect.first().selectOption('ACTIVE');
      await page.waitForTimeout(500);
    }
  });
});
