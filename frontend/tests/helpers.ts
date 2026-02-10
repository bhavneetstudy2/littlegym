import { Page } from '@playwright/test';

const BACKEND_URL = 'http://localhost:8000';

/**
 * Login via direct API call and set localStorage tokens.
 * This bypasses the React hydration issues with form-based login in Playwright.
 */
export async function loginViaAPI(
  page: Page,
  email = 'admin@littlegym.com',
  password = 'admin123'
) {
  // Navigate to app first so we're on the right origin for localStorage
  await page.goto('/login', { waitUntil: 'domcontentloaded' });

  const loginResult = await page.evaluate(
    async ({ url, email, password }) => {
      try {
        const response = await fetch(`${url}/api/v1/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password }),
        });

        if (!response.ok) {
          return { success: false, error: `HTTP ${response.status}` };
        }

        const data = await response.json();
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        return { success: true, user: data.user };
      } catch (err: any) {
        return { success: false, error: err.message };
      }
    },
    { url: BACKEND_URL, email, password }
  );

  if (!loginResult.success) {
    throw new Error(`Login failed: ${loginResult.error}`);
  }

  return loginResult;
}

/**
 * Login and navigate to a specific page, waiting for it to be ready.
 */
export async function loginAndNavigateTo(page: Page, path: string) {
  await loginViaAPI(page);

  // Navigate to the target page
  await page.goto(path, { waitUntil: 'domcontentloaded' });

  // Wait for the page to move past the "Loading..." state
  // AppLayout shows "Loading..." while checking auth, then renders content
  await page.waitForFunction(
    () => {
      const body = document.body.textContent || '';
      return !body.includes('Loading...') || body.length > 20;
    },
    { timeout: 10000 }
  );

  // Small additional wait for React to stabilize
  await page.waitForTimeout(500);
}

/**
 * Wait for page content to be visible (not stuck in loading state)
 */
export async function waitForPageReady(page: Page) {
  await page.waitForFunction(
    () => {
      const loading = document.querySelector('.text-gray-500');
      if (loading && loading.textContent === 'Loading...') return false;
      return document.body.children.length > 0;
    },
    { timeout: 10000 }
  );
  await page.waitForTimeout(300);
}
