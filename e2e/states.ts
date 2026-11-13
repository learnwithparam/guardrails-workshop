// The desk page after the learner picks an email and runs the desk on it.
import type { Page } from "@playwright/test";

export type PageState = { name: string; path: string; prepare: (page: Page) => Promise<void> };

export const states: PageState[] = [
  {
    name: "desk page with an email open",
    path: "/",
    prepare: async (page) => {
      await page.locator(".mail").first().click();
      await page.locator("#go").waitFor();
    },
  },
  {
    name: "desk page after a run",
    path: "/",
    prepare: async (page) => {
      await page.locator(".mail").first().click();
      await page.locator("#go").click();
      await page.locator("#run .note").waitFor();
    },
  },
];
