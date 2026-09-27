import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "tests/browser",
  workers: 1,
  retries: 0,
  use: { baseURL: "http://127.0.0.1:8100", trace: "retain-on-failure" },
  webServer: {
    command:
      "uv run --frozen python scripts/prepare-browser.py && uv run --frozen python manage.py runserver 127.0.0.1:8100 --noreload --settings=config.settings_browser",
    url: "http://127.0.0.1:8100/health/",
    reuseExistingServer: false,
    env: { APP_ENV: "test" },
  },
});
