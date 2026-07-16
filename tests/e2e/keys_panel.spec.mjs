// Model-keys UX — the app SAYS what's configured and takes keys in-app (real Chromium).
// Adaptive to the stack it meets:
//   mock stack (CI fixture) → asserts the mock badge is visible in the AI panel;
//   keyless live stack      → full flow: "needs a key" notice → ＋ Add keys → save →
//                             status flips to ready, value never echoed (masked tail only).
// NEVER run the keyless flow against a configured stack: it would write dummy keys
// into that stack's env file. The spec checks status first and skips accordingly.
import { chromium } from 'playwright';

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1500, height: 850 } });
await page.goto('http://localhost:5173/');
await page.waitForFunction(() => document.getElementById('model-status').textContent.length > 0, null, { timeout: 15000 });

const fail = async (msg) => {
  await page.screenshot({ path: 'tests/screenshots/keys_panel_FAIL.png' });
  console.error(`FAIL: ${msg}`);
  await browser.close();
  process.exit(1);
};

const statusText = await page.locator('#model-status').textContent();

if (statusText.includes('mock mode')) {
  // CI / mock stack: the badge IS the feature here — the app discloses simulation.
  await page.screenshot({ path: 'tests/screenshots/keys_panel_mock_badge.png' });
  console.log('PASS (mock stack): mock badge visible in the AI panel');
  await browser.close();
  process.exit(0);
}

if (!statusText.includes('needs a')) {
  console.log('SKIP: stack already has keys configured — keyless flow not exercised');
  await browser.close();
  process.exit(0);
}

// ── Keyless stack: the full in-app flow ──────────────────────────────────────
if (!/env/.test(statusText)) await fail('unconfigured notice does not point at the env file');
await page.screenshot({ path: 'tests/screenshots/keys_panel_unconfigured.png' });

await page.click('#model-status a');                       // ＋ Add keys here
await page.waitForSelector('#keyform', { state: 'visible' });
await page.fill('#key-anthropic', 'sk-ant-e2e-test-1234abcd');
await page.fill('#key-openai', 'sk-e2e-test-9999wxyz');
await page.click('#keyform .aibtn');
await page.waitForFunction(
  () => document.getElementById('model-status').textContent.includes('ready'),
  null, { timeout: 10000 });

const after = await page.locator('#model-status').textContent();
if (!after.includes('✦') || !(after.match(/ready/g) || []).length === 2) await fail('status did not flip to ready for both models');
if (after.includes('sk-ant-e2e-test-1234abcd')) await fail('key VALUE echoed into the UI');
if (!after.includes('…abcd')) await fail('masked key tail missing from the ready line');
const note = await page.locator('#keyform-note').textContent();
if (!note.includes('saved')) await fail('save confirmation note missing');

await page.screenshot({ path: 'tests/screenshots/keys_panel_configured.png' });
console.log('PASS (keyless stack): notice → add keys → live, masked, never echoed');
await browser.close();
