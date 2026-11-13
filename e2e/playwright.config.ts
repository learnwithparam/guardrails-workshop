// The audit needs the course app running. Set AUDIT_URL to where it listens.
// Set AUDIT_SERVER to a command that starts it, and Playwright starts and stops it for you.
import { defineConfig } from "@playwright/test";

const appUrl = process.env.AUDIT_URL ?? "http://127.0.0.1:8300";
const startCommand = process.env.AUDIT_SERVER ?? "uv run desk serve --reference";

export default defineConfig({
  testDir: ".",
  testMatch: "text-audit.spec.ts",
  reporter: "list",
  use: {
    // biome-ignore lint/style/useNamingConvention: baseURL is the name Playwright requires
    baseURL: appUrl,
    trace: "off",
    // AUDIT_BROWSER: path to a Chrome you already have, if the Playwright download fails.
    launchOptions: process.env.AUDIT_BROWSER ? { executablePath: process.env.AUDIT_BROWSER } : {},
  },
  webServer: startCommand
    ? { command: startCommand, url: appUrl, reuseExistingServer: true }
    : undefined,
});
