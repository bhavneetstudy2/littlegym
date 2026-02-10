import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Clear storage
    await page.goto('http://localhost:3000');
    await page.evaluate(() => localStorage.clear());
  });

  test('should redirect to login when not authenticated', async ({ page }) => {
    await page.goto('http://localhost:3000/dashboard');
    // Should be redirected to login
    await page.waitForURL(/\/login/, { timeout: 10000 });
    expect(page.url()).toContain('/login');
  });

  test('should login successfully with valid credentials', async ({ page }) => {
    await page.goto('http://localhost:3000/login');
    await page.waitForLoadState('domcontentloaded');

    // Directly call the login API using page.evaluate
    const loginResult = await page.evaluate(async () => {
      try {
        const response = await fetch('http://localhost:8000/api/v1/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: 'admin@littlegym.com',
            password: 'admin123'
          })
        });

        if (!response.ok) {
          return { success: false, error: await response.text() };
        }

        const data = await response.json();

        // Store in localStorage like the real login does
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));

        return { success: true, user: data.user };
      } catch (err: any) {
        return { success: false, error: err.message };
      }
    });

    expect(loginResult.success).toBe(true);

    // Now navigate to dashboard
    await page.goto('http://localhost:3000/dashboard');

    // Should stay on dashboard (not redirect to login)
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 5000 });

    // Verify we can see dashboard content
    await expect(page.locator('text=Welcome')).toBeVisible({ timeout: 5000 });
  });

  test('should show error with invalid credentials', async ({ page }) => {
    await page.goto('http://localhost:3000/login');
    await page.waitForLoadState('domcontentloaded');

    const loginResult = await page.evaluate(async () => {
      const response = await fetch('http://localhost:8000/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: 'wrong@email.com',
          password: 'wrongpass'
        })
      });

      return {
        ok: response.ok,
        status: response.status
      };
    });

    expect(loginResult.ok).toBe(false);
    expect(loginResult.status).toBe(401);
  });

  test('should logout successfully', async ({ page }) => {
    // Login first using direct API call
    await page.goto('http://localhost:3000/login');

    await page.evaluate(async () => {
      const response = await fetch('http://localhost:8000/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: 'admin@littlegym.com',
          password: 'admin123'
        })
      });
      const data = await response.json();
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));
    });

    // Go to dashboard
    await page.goto('http://localhost:3000/dashboard');
    await expect(page).toHaveURL(/\/dashboard/);

    // Click logout
    await page.click('text=Logout');

    // Should redirect to login
    await expect(page).toHaveURL(/\/login/, { timeout: 5000 });

    // Verify token is cleared
    const token = await page.evaluate(() => localStorage.getItem('access_token'));
    expect(token).toBeNull();
  });
});
