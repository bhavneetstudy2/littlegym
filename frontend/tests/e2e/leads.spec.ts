import { test, expect } from '@playwright/test';

test.describe('Leads Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.fill('input[type="email"]', 'admin@littlegym.com');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');
  });

  test('should navigate to leads page', async ({ page }) => {
    await page.click('text=Leads');
    await expect(page).toHaveURL('/leads');
    await expect(page.locator('h1')).toContainText('Leads Management');
  });

  test('should open create lead modal', async ({ page }) => {
    await page.goto('/leads');
    await page.click('text=+ New Lead');

    // Modal should be visible
    await expect(page.locator('text=Create New Lead')).toBeVisible();
  });

  test('should create a new lead', async ({ page }) => {
    await page.goto('/leads');
    await page.click('text=+ New Lead');

    // Fill child information
    await page.fill('input[name="child_first_name"]', 'Test');
    await page.fill('input[name="child_last_name"]', 'Child');
    await page.fill('input[type="date"]', '2020-01-15');
    await page.fill('input[placeholder*="school"]', 'Test School');

    // Fill parent information
    await page.fill('input[placeholder*="Parent Name"]', 'Test Parent');
    await page.fill('input[type="tel"]', '9876543210');
    await page.fill('input[type="email"]', 'parent@test.com');

    // Select source
    await page.selectOption('select', 'WALK_IN');

    // Submit form
    await page.click('button:has-text("Create Lead")');

    // Should close modal and show success
    await expect(page.locator('text=Create New Lead')).not.toBeVisible({ timeout: 5000 });

    // Should show the new lead in the list
    await expect(page.locator('text=Test Child')).toBeVisible({ timeout: 5000 });
  });

  test('should filter leads by status', async ({ page }) => {
    await page.goto('/leads');

    // Click on a status filter
    await page.click('button:has-text("DISCOVERY")');

    // URL or UI should reflect the filter
    await expect(page.locator('.bg-blue-600')).toContainText('DISCOVERY');
  });

  test('should search leads by name', async ({ page }) => {
    await page.goto('/leads');

    // Type in search box
    await page.fill('input[placeholder*="Search"]', 'Test');

    // Should filter results
    await page.waitForTimeout(500); // Debounce
  });
});
