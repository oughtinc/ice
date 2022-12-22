import type { Meta, StoryObj } from "@storybook/react";

import { flattenFString, FString } from "./FString";

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

export const Nested: Story = {
  args: {
    parts: flattenFString([
      "Hello ",
      {
        source: "inner",
        value: {
          __fstring__: [
            "inner ",
            {
              __fstring__: ["inmost ", { source: "1", value: "1", formatted: "1" }],
            },
            { source: "2", value: "2", formatted: "2" },
          ],
        },
        formatted: "inner inmost 12",
      },
      { source: "3", value: "3", formatted: "3" },
      ".",
    ]),
  },
};
