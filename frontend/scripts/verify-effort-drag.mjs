import { chromium } from "playwright-core";
import { fileURLToPath } from "node:url";
import { resolve } from "node:path";

const baseUrl = process.env.RAGENT_URL ?? "http://127.0.0.1:2002";
const browser = await chromium.launch({ channel: "msedge", headless: true });
let original;
let sessionId;
let created = false;

try {
  const page = await browser.newPage({ viewport: { width: 1600, height: 960 } });
  page.on("pageerror", (error) => console.error(`page error: ${error.message}`));
  page.on("console", (message) => message.type() === "error" && console.error(`browser console: ${message.text()}`));
  page.on("response", (response) => response.status() >= 400 && console.error(`HTTP ${response.status()}: ${response.url()}`));
  await page.goto(`${baseUrl}/studio`, { waitUntil: "networkidle" });
  await page.getByRole("button", { name: /新建对话/ }).waitFor();
  await page.locator(".side-actions .icon").click();
  await page.locator(".quota-panel").waitFor();
  await page.getByRole("button", { name: "关闭" }).click();

  const sessions = await page.request.get(`${baseUrl}/studio-api/sessions`).then((r) => r.json());
  let session = sessions.find((item) => item.status !== "running");
  if (!session) {
    const repoRoot = resolve(fileURLToPath(new URL("../..", import.meta.url)));
    const response = await page.request.post(`${baseUrl}/studio-api/sessions`, { data: {
      repo_root: repoRoot,
      provider: "deepseek",
      model: "deepseek-v4-flash",
      reasoning_effort: "high",
    } });
    if (!response.ok()) throw new Error(`创建交互测试会话失败：HTTP ${response.status()}`);
    session = await response.json();
    session = await page.request.get(`${baseUrl}/studio-api/sessions/${session.session_id}`).then((r) => r.json());
    created = true;
    await page.reload({ waitUntil: "networkidle" });
  }
  sessionId = session.session_id;
  original = session;

  await page.locator(".session-row", { hasText: session.title }).locator("button").first().click();
  const slider = page.locator('.composer input[type="range"]');
  await slider.waitFor({ state: "visible" });
  if (await slider.isDisabled()) throw new Error("空闲会话的推理强度不应锁定");

  const max = Number(await slider.getAttribute("max"));
  const current = Number(await slider.inputValue());
  const targetIndex = current === 0 ? max : 0;
  const target = session.provider === "openai"
    ? ["none", "low", "medium", "high", "xhigh", "max"][targetIndex]
    : ["low", "high", "max"][targetIndex];

  const responsePromise = page.waitForResponse((response) =>
    response.url().endsWith(`/studio-api/sessions/${sessionId}/settings`) &&
    response.request().method() === "PATCH" && response.ok(),
  );
  const box = await slider.boundingBox();
  if (!box) throw new Error("无法读取推理强度滑块位置");
  const targetX = box.x + (targetIndex / Math.max(1, max)) * box.width;
  await page.mouse.move(box.x + (current / Math.max(1, max)) * box.width, box.y + box.height / 2);
  await page.mouse.down();
  await page.mouse.move(targetX, box.y + box.height / 2, { steps: 12 });
  await page.mouse.up();
  await responsePromise;
  const updated = await page.request.get(`${baseUrl}/studio-api/sessions/${sessionId}`).then((r) => r.json());
  if (updated.reasoning_effort !== target) throw new Error(`拖动未生效：期望 ${target}，实际 ${updated.reasoning_effort}`);
  console.log(`React workbench verified: ${original.reasoning_effort} -> ${target}`);
} finally {
  if (sessionId && original) {
    const context = browser.contexts()[0];
    await context?.request.patch(`${baseUrl}/studio-api/sessions/${sessionId}/settings`, {
      data: {
        provider: original.provider,
        model: original.model,
        reasoning_effort: original.reasoning_effort,
        verification_mode: original.verification_mode,
        test_command: original.test_command,
      },
    });
    if (created) await context?.request.delete(`${baseUrl}/studio-api/sessions/${sessionId}`);
  }
  await browser.close();
}
