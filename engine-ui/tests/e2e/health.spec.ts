import { expect, test } from "@playwright/test";

test.describe("Health Check", () => {
  test("backend health endpoint returns ok", async ({ request }) => {
    const apiUrl =
      process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
    const resp = await request.get(`${apiUrl}/health`);
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body.status).toBe("ok");
  });

  test("frontend loads homepage", async ({ page }) => {
    await page.goto("/");
    await expect(
      page.getByText("Training Program Generator")
    ).toBeVisible();
  });
});
