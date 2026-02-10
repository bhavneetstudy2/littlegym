import { test } from '@playwright/test';

test('check what happens on dashboard without auth', async ({ page }) => {
  await page.goto('http://localhost:3000');
  await page.evaluate(() => localStorage.clear());

  await page.goto('http://localhost:3000/dashboard', { waitUntil: 'networkidle' });

  console.log('Final URL:', page.url());

  const html = await page.content();
  console.log('Page contains "login":', html.includes('login'));
  console.log('Page contains "dashboard":', html.includes('dashboard'));
  console.log('Page contains "Loading":', html.includes('Loading'));

  // Take screenshot
  await page.screenshot({ path: 'test-results/dashboard-without-auth.png' });
});

test('check dashboard WITH auth', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Login via API
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

  await page.goto('http://localhost:3000/dashboard', { waitUntil: 'networkidle' });

  console.log('Final URL:', page.url());

  const html = await page.content();
  console.log('Page contains "Welcome":', html.includes('Welcome'));
  console.log('Page contains "Dashboard":', html.includes('Dashboard'));
  console.log('Page contains "Logout":', html.includes('Logout'));

  // Take screenshot
  await page.screenshot({ path: 'test-results/dashboard-with-auth.png' });
});
