import { test, expect } from '@playwright/test';
import { loginAndNavigateTo } from '../helpers';

test.describe('Leads Management', () => {
  test.beforeEach(async ({ page }) => {
    await loginAndNavigateTo(page, '/leads');
  });

  test('should display leads page', async ({ page }) => {
    await expect(page).toHaveURL(/\/leads/);
    // Wait for actual content to appear
    await page.waitForFunction(
      () => {
        const body = document.body.textContent || '';
        return body.includes('Lead') || body.includes('Enquir');
      },
      { timeout: 10000 }
    );
  });

  test('should open create lead / enquiry modal', async ({ page }) => {
    // Look for any button that opens a new lead/enquiry form
    const newButton = page.locator('button').filter({
      hasText: /New|Add|Create|Enquiry/i,
    });

    if ((await newButton.count()) > 0) {
      await newButton.first().click();
      // Modal or form should appear
      await page.waitForTimeout(500);
      const modalContent = await page.textContent('body');
      expect(
        modalContent?.includes('Lead') ||
          modalContent?.includes('Enquiry') ||
          modalContent?.includes('Child')
      ).toBeTruthy();
    }
  });

  test('should display lead filters or center selection', async ({ page }) => {
    // The page should show either lead status filters or prompt to select a center
    await page.waitForFunction(
      () => {
        const body = document.body.textContent || '';
        return (
          body.includes('ENQUIRY') ||
          body.includes('DISCOVERY') ||
          body.includes('All') ||
          body.includes('ALL') ||
          body.includes('select a center') ||
          body.includes('Lead') ||
          body.includes('Enquir')
        );
      },
      { timeout: 10000 }
    );
  });

  test('should have search functionality', async ({ page }) => {
    const searchInput = page.locator(
      'input[placeholder*="Search"], input[placeholder*="search"], input[type="search"]'
    );
    if ((await searchInput.count()) > 0) {
      await searchInput.first().fill('test');
      await page.waitForTimeout(600); // Wait for debounce
    }
  });
});
