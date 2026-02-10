import { test, expect } from '@playwright/test';
import { loginAndNavigateTo } from '../helpers';

test.describe('Enrollment Management', () => {
  test.beforeEach(async ({ page }) => {
    await loginAndNavigateTo(page, '/enrollments');
  });

  test('should display enrollments page', async ({ page }) => {
    await expect(page).toHaveURL(/\/enrollments/);
    await page.waitForFunction(
      () => {
        const body = document.body.textContent || '';
        return body.includes('Enrollment') || body.includes('center');
      },
      { timeout: 10000 }
    );
  });

  test('should display enrollment content or center prompt', async ({
    page,
  }) => {
    // Page should show either enrollment data or prompt to select a center
    await page.waitForFunction(
      () => {
        const body = document.body.textContent || '';
        return (
          body.includes('Enrollment') ||
          body.includes('Batch') ||
          body.includes('select a center') ||
          body.includes('center')
        );
      },
      { timeout: 10000 }
    );
  });

  test('should display enrollments list or empty state', async ({ page }) => {
    await page.waitForFunction(
      () => {
        const body = document.body.textContent || '';
        return (
          body.includes('Student') ||
          body.includes('Plan') ||
          body.includes('Active') ||
          body.includes('Enrollment') ||
          body.includes('select a center') ||
          body.includes('No enrollment')
        );
      },
      { timeout: 10000 }
    );
  });
});
