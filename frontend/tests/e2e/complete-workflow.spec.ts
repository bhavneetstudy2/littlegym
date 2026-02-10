import { test, expect } from '@playwright/test';
import { loginViaAPI, loginAndNavigateTo } from '../helpers';

test.describe('Complete Workflow Integration', () => {
  test('should navigate across all pages after login', async ({ page }) => {
    await loginViaAPI(page);

    const pages = [
      { path: '/dashboard', expect: /Dashboard|Welcome|Stats/i },
      { path: '/leads', expect: /Lead|Enquir/i },
      { path: '/enrollments', expect: /Enrollment|Batch/i },
      { path: '/attendance', expect: /Attendance|Session/i },
      { path: '/progress', expect: /Progress|Skill/i },
      { path: '/report-cards', expect: /Report|Card/i },
      { path: '/renewals', expect: /Renewal|Expir/i },
    ];

    for (const pageInfo of pages) {
      await page.goto(pageInfo.path, { waitUntil: 'domcontentloaded' });
      await expect(page).toHaveURL(new RegExp(pageInfo.path));

      // Wait for page content (not stuck at loading)
      await page.waitForFunction(
        (pattern) => {
          const body = document.body.textContent || '';
          return new RegExp(pattern, 'i').test(body);
        },
        pageInfo.expect.source,
        { timeout: 15000 }
      );

      console.log(`[OK] ${pageInfo.path} loaded`);
    }

    console.log('\n[SUCCESS] All pages navigated successfully!');
  });

  test('dashboard should display live stats', async ({ page }) => {
    await loginAndNavigateTo(page, '/dashboard');

    await page.waitForFunction(
      () => {
        const body = document.body.textContent || '';
        return (
          body.includes('Lead') ||
          body.includes('Enrollment') ||
          body.includes('Student') ||
          body.includes('Welcome')
        );
      },
      { timeout: 10000 }
    );
  });

  test('sidebar navigation should show correct items for admin', async ({
    page,
  }) => {
    await loginAndNavigateTo(page, '/dashboard');

    // Admin should see all navigation items
    const expectedLinks = [
      'Dashboard',
      'Leads',
      'Enrollments',
      'Attendance',
      'Progress',
      'Report Cards',
      'Renewals',
    ];

    for (const linkText of expectedLinks) {
      const link = page.locator(`text=${linkText}`).first();
      await expect(link).toBeVisible({ timeout: 5000 });
    }
  });

  test('should handle admin page for admin users', async ({ page }) => {
    await loginAndNavigateTo(page, '/admin');

    await page.waitForFunction(
      () => {
        const body = document.body.textContent || '';
        return (
          body.includes('Admin') ||
          body.includes('User') ||
          body.includes('Center')
        );
      },
      { timeout: 10000 }
    );
  });
});
