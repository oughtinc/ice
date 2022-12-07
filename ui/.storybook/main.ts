import type { StorybookConfig } from "@storybook/types";

const config: StorybookConfig = {
  stories: ["../components/**/*.stories.tsx"],
  addons: [
    "@storybook/addon-links",
    "@storybook/addon-essentials",
    "@storybook/addon-interactions",
  ],
  framework: {
    name: "@storybook/react-vite",
  },
  refs: {
    "@chakra-ui/react": {
      disable: true,
    },
  },
};

export default config;
