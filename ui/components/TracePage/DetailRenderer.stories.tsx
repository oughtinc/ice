import type { Meta, StoryObj } from "@storybook/react";

import { DetailRenderer } from "./DetailRenderer";

const meta: Meta<typeof DetailRenderer> = {
  title: "TracePage/DetailRenderer",
  component: DetailRenderer,
};

export default meta;

type Story = StoryObj<typeof DetailRenderer>;

// TODO how to set up a storybook test for this? such that the clicks are handled

export const Nested: Story = {
  args: {
    data: {
      foo: "bar",
      baz: {
        __fstring__: [
          "inner ",
          {
            __fstring__: ["inmost ", { source: "1", value: "1", formatted: "1" }],
          },
          { source: "2", value: "2", formatted: "2" },
        ],
      },
      qux: [1, 2, 3],
      oneElement: [1],
      emptyArray: [],
      emptyObject: {},
      duplicateName: [500],
      // TODO add some validation about fstrings- easy to break this; maybe just types ?
      containingDuplicateName: {
        duplicateName: [501],
      },
    },
  },
};
