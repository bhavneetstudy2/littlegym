import { test, expect } from '@playwright/test';
import { loginViaAPI } from '../helpers';

test.describe('Authentication Flow - Simple', () => {
  test('can load login page', async ({ page }) => {
    await page.goto('http://localhost:3000/login');
    await expect(page.locator('h1')).toContainText('The Little Gym CRM');
    await expect(page.locator('input#email')).toBeVisible();
    await expect(page.locator('input#password')).toBeVisible();
  });

  test('can login with valid credentials', async ({ page }) => {
    // Use API-based login to bypass React hydration timing issues
    const result = await loginViaAPI(page);
    expect(result.success).toBe(true);

    // Navigate to dashboard and verify it loads
    await page.goto('http://localhost:3000/dashboard');
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });

    // Verify dashboard content appears
    await page.waitForFunction(
      () => {
        const body = document.body.textContent || '';
        return body.includes('Welcome') || body.includes('Dashboard');
      },
      { timeout: 10000 }
    );
  });
});
