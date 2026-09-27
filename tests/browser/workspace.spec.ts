import { test, expect } from "@playwright/test";

test("sign in, private notes, validation and sign out", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await expect(page).toHaveURL(/login/);
  await page.getByLabel("Username").fill("browser-member");
  await page.getByLabel("Password").fill("wrong-password");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByRole("alert")).toBeVisible();
  await page.getByLabel("Password").fill("browser-test-password");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByRole("heading", { name: "A place to start." })).toBeVisible();
  await expect(page.getByRole("link", { name: "Admin", exact: true })).toHaveCount(0);
  await page.getByLabel("New note").fill("   ");
  await page.getByRole("button", { name: "Add note" }).click();
  await expect(page.getByLabel("New note")).toHaveAttribute("aria-invalid", "true");
  await page.getByLabel("New note").fill("A private browser note");
  await page.getByRole("button", { name: "Add note" }).click();
  await expect(page.getByText("A private browser note", { exact: true })).toBeVisible();
  await expect(page.getByLabel("New note")).toHaveValue("");
  await expect(page.getByRole("status")).toHaveText("Note added");
  await page.getByRole("button", { name: "Delete", exact: true }).click();
  await expect(page.getByText("Your notes will appear here. Only you can see them.")).toBeVisible();
  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page.getByRole("heading", { name: "Welcome back" })).toBeVisible();
  expect(errors).toEqual([]);
});

test("admin navigation uses the Django admin page", async ({ page }) => {
  await page.goto("/login/");
  await page.getByLabel("Username").fill("browser-admin");
  await page.getByLabel("Password").fill("browser-test-password");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await page.getByRole("link", { name: "Admin", exact: true }).click();
  await expect(page).toHaveURL(/admin\/$/);
  await expect(page.getByRole("heading", { name: "Site administration" })).toBeVisible();
});
