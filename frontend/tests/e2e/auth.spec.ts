import { test, expect } from '@playwright/test';
import { loginViaAPI } from '../helpers';

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Clear storage
    await page.goto('/');
    await page.evaluate(() => localStorage.clear());
  });

  test('should redirect to login when not authenticated', async ({ page }) => {
    await page.goto('/dashboard');
    // AppLayout checks token and redirects to login
    await page.waitForURL(/\/login/, { timeout: 10000 });
    expect(page.url()).toContain('/login');
  });

  test('should login successfully via API', async ({ page }) => {
    const result = await loginViaAPI(page);
    expect(result.success).toBe(true);

    // Navigate to dashboard
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });

    // Verify dashboard content loads (not stuck at Loading...)
    await page.waitForFunction(
      () => {
        const body = document.body.textContent || '';
        return body.includes('Welcome') || body.includes('Dashboard');
      },
      { timeout: 10000 }
    );
  });

  test('should reject invalid credentials', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('domcontentloaded');

    const loginResult = await page.evaluate(async () => {
      const response = await fetch('http://localhost:8000/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: 'wrong@email.com',
          password: 'wrongpass',
        }),
      });
      return { ok: response.ok, status: response.status };
    });

    expect(loginResult.ok).toBe(false);
    expect(loginResult.status).toBe(401);
  });

  test('should logout successfully', async ({ page }) => {
    // Login first
    await loginViaAPI(page);

    // Go to dashboard
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/dashboard/);

    // Wait for sidebar to render with Logout button
    await page.waitForFunction(
      () => document.body.textContent?.includes('Logout'),
      { timeout: 10000 }
    );

    // Click logout
    await page.click('text=Logout');

    // Should redirect to login
    await expect(page).toHaveURL(/\/login/, { timeout: 10000 });

    // Verify token is cleared
    const token = await page.evaluate(() =>
      localStorage.getItem('access_token')
    );
    expect(token).toBeNull();
  });
});
