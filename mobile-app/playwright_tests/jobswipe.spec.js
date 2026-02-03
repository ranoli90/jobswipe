const { test, expect } = require('@playwright/test');

test('JobSwipe Web App Test', async ({ page }) => {
  // Enable automatic screenshot capture on failure
  test.slow(); // Extend timeout for Flutter apps
  
  // Record video and trace for debugging
  await page.context().tracing.start({
    screenshots: true,
    snapshots: true
  });

  try {
    // Navigate to running app
    await page.goto('http://localhost:8082');
    
    // Basic UI validation
    await expect(page.getByText('JobSwipe')).toBeVisible({ timeout: 15000 });
    
    // Take screenshot of initial state
    await page.screenshot({ path: 'initial-state.png' });
    
    // Add your test interactions here
    // Example: await page.click('button:has-text("Sign In")');
    
    // More verifications...
  } catch (error) {
    // Capture screenshot on error
    await page.screenshot({ path: 'error-state.png' });
    throw error;
  } finally {
    // Save trace
    await page.context().tracing.stop({ path: 'trace.zip' });
  }
});
