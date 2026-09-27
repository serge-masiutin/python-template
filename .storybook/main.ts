import type { StorybookConfig } from "@storybook/react-vite";
const config: StorybookConfig = {
  core: { disableTelemetry: true },
  stories: ["../web/src/**/*.stories.tsx"],
  addons: ["@storybook/addon-a11y", "@storybook/addon-docs", "@storybook/addon-vitest"],
  framework: "@storybook/react-vite",
  staticDirs: ["../web/public"],
};
export default config;
