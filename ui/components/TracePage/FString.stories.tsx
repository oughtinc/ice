import type { Meta, StoryObj } from "@storybook/react";

import { FString } from "./FString";

const meta: Meta<typeof FString> = {
  title: "TracePage/FString",
  component: FString,
};

export default meta;
type Story = StoryObj<typeof FString>;

export const HelloWorld: Story = {
  args: {
    parts: [
      "Hello ",
      { source: "name", value: "world", formatted: "world" },
      ", goodbye ",
      {
        source: "name",
        value: "world",
        formatted: "world",
      },
      ".",
    ],
  },
};
