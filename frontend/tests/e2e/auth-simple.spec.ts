import { test, expect } from '@playwright/test';

test.describe('Authentication Flow - Simple', () => {
  test('can load login page', async ({ page }) => {
    await page.goto('http://localhost:3000/login');
    await expect(page.locator('h1')).toContainText('The Little Gym CRM');
    await expect(page.locator('input#email')).toBeVisible();
    await expect(page.locator('input#password')).toBeVisible();
  });

  test('can login with valid credentials', async ({ page }) => {
    await page.goto('http://localhost:3000/login');

    // Wait for page to be ready
    await page.waitForLoadState('domcontentloaded');
    await page.waitForSelector('button[type="submit"]');

    // Fill form
    await page.locator('input#email').fill('admin@littlegym.com');
    await page.locator('input#password').fill('admin123');

    // Listen for the API call
    const responsePromise = page.waitForResponse(
      response => response.url().includes('/api/v1/auth/login') && response.status() === 200
    );

    // Click submit
    await page.locator('button[type="submit"]').click();

    // Wait for successful login API call
    await responsePromise;

    // Wait for navigation
    await page.waitForURL('http://localhost:3000/dashboard', { timeout: 10000 });

    // Verify we're on dashboard
    expect(page.url()).toContain('/dashboard');
  });
});
