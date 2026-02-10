import { Page } from '@playwright/test';

/**
 * Wait for Next.js page to be fully hydrated and interactive
 */
export async function waitForHydration(page: Page) {
  try {
    // Wait for Next.js to be ready
    await page.waitForFunction(() => {
      return (window as any).next && (window as any).next.router;
    }, { timeout: 10000 });
  } catch {
    // Fallback: just wait for load state
    await page.waitForLoadState('networkidle');
  }

  // Additional wait for React to attach event handlers
  await page.waitForTimeout(500);
}

/**
 * Login helper for tests
 */
export async function login(page: Page, email: string, password: string) {
  await page.goto('/login', { waitUntil: 'networkidle' });
  await waitForHydration(page);

  await page.fill('input#email', email);
  await page.fill('input#password', password);

  // Click submit and wait for navigation
  const [response] = await Promise.all([
    page.waitForResponse(resp => resp.url().includes('/api/v1/auth/login'), { timeout: 10000 }),
    page.click('button[type="submit"]')
  ]);

  // If login successful, wait for dashboard
  if (response.ok()) {
    await page.waitForURL('/dashboard', { timeout: 10000 });
    await waitForHydration(page);
  }

  return response.ok();
}
