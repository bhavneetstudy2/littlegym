import { test, expect } from '@playwright/test';

test('debug login form submission', async ({ page }) => {
  // Enable console logging
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', error => console.log('PAGE ERROR:', error.message));

  await page.goto('http://localhost:3000/login');
  await page.waitForLoadState('networkidle');

  console.log('Page loaded, URL:', page.url());

  // Check if form has onSubmit handler
  const hasHandler = await page.evaluate(() => {
    const form = document.querySelector('form');
    return {
      formExists: !!form,
      hasOnSubmit: form?.onsubmit !== null,
      formAction: form?.action || 'none',
      formMethod: form?.method || 'none'
    };
  });
  console.log('Form info:', hasHandler);

  // Wait a bit for React hydration
  await page.waitForTimeout(3000);

  // Check again after hydration
  const hasHandlerAfter = await page.evaluate(() => {
    const form = document.querySelector('form');
    return {
      formExists: !!form,
      hasOnSubmit: form?.onsubmit !== null,
      formAction: form?.action || 'none',
      formMethod: form?.method || 'none'
    };
  });
  console.log('Form info after hydration:', hasHandlerAfter);

  // Try to submit
  await page.locator('input#email').fill('admin@littlegym.com');
  await page.locator('input#password').fill('admin123');

  console.log('Form filled, about to click submit...');

  // Log network requests
  page.on('request', request => {
    if (request.url().includes('login')) {
      console.log('REQUEST:', request.method(), request.url());
    }
  });
  page.on('response', response => {
    if (response.url().includes('login')) {
      console.log('RESPONSE:', response.status(), response.url());
    }
  });

  await page.locator('button[type="submit"]').click();

  console.log('Clicked submit, waiting...');

  await page.waitForTimeout(5000);

  console.log('Final URL:', page.url());
});
